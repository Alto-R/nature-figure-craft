"""
profile_data.py -- read a data file and report what figures it can support.

Step 0 of chart selection. Run this BEFORE proposing anything, so the proposal
is grounded in the actual columns, cardinalities and group sizes rather than in
a guess about what a file called `results.xlsx` probably contains.

    python profile_data.py results.xlsx
    python profile_data.py results.xlsx --sheet Fig2 --json profile.json

What it detects, and why each one matters
-----------------------------------------
geo pair          lat/lon columns          -> a map is available at all
temporal column   datetime or year-like    -> trend charts are available
entity column     high-cardinality id      -> "one mark = one entity" is possible
scenario column   low-cardinality, repeats  -> repeated measures; uncertainty
                  every entity                must be shown, paired designs open
wide scenarios    shared-prefix columns     -> same, in wide form (slope, sankey)
composition set   parts that sum to a total -> stacked / share charts are honest
group sizes       n per category            -> reported raw; NO cutoff is applied,
                                               because a cutoff changes what number
                                               the figure can state (see below)
skew / range      max/median ratio          -> log axis, or the value is a tail

The output is deliberately a menu of what is POSSIBLE, not a recommendation.
Choosing among the possibilities requires the claim, which the data cannot
supply.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

import numpy as np
import pandas as pd

LAT_RE = re.compile(r"^(lat|latitude|y_?coord)$", re.I)
LON_RE = re.compile(r"^(lon|lng|long|longitude|x_?coord)$", re.I)
TIME_RE = re.compile(r"(year|date|time|month|day|hour|period|step|epoch)", re.I)
ID_RE = re.compile(r"(^id$|_id$|^index$|uuid|code$)", re.I)

# Tunables. All three are rules of thumb, not findings. They are named and
# exposed rather than inlined so that a run which depends on one can say so.
MAX_NOMINAL = 60          # above this a categorical is an entity list, not a facet
COMP_TOL = 0.02           # relative tolerance when testing whether parts sum to a total
COMP_HIT_RATE = 0.95      # fraction of rows that must satisfy that sum
SKEW_TAIL_RATIO = 8       # max/median above this is reported as long-tailed

# There is deliberately NO small-group threshold here.
#
# An earlier version carried SMALL_GROUP = 30 and used it to emit a *settled*
# verdict ("these groups are too small for a density -- plot the points") and
# to gate which groups were worth splitting on. That was wrong twice over.
# The number had no provenance -- it was not derived from anything -- yet it
# silently decided how many groups survived, which statistic was defensible,
# and therefore what headline number the paper could state. A threshold that
# consequential must be a recorded decision made by the person writing the
# paper, not a constant buried in a profiler.
#
# So the profiler now reports the raw group sizes and stops. Choosing a cutoff
# (or choosing not to cut) is Step 2 work, and whatever is chosen has to be
# written down in the decisions record with its reason.


def _kind(s: pd.Series, name: str, n_rows: int) -> str:
    if LAT_RE.match(name):
        return "latitude"
    if LON_RE.match(name):
        return "longitude"
    if pd.api.types.is_datetime64_any_dtype(s):
        return "temporal"
    nun = s.nunique(dropna=True)
    if pd.api.types.is_numeric_dtype(s):
        if TIME_RE.search(name) and nun <= 300:
            return "temporal"
        if ID_RE.search(name):
            return "identifier"
        # All-unique is NOT evidence of an identifier for floats -- a real
        # continuous measurement is all-unique by construction. Only integers
        # that happen to enumerate the rows are identifiers.
        if pd.api.types.is_integer_dtype(s) and nun == n_rows and nun > 20:
            return "identifier"
        return "continuous"
    if nun == n_rows and nun > 20:
        return "identifier"
    return "categorical"


def _shared_prefix_groups(cols) -> dict:
    """Wide-format scenario families: value_t0 / value_t1 / value_t2."""
    fams = {}
    for c in cols:
        for sep in ("_", ".", "-"):
            if sep in c:
                stem, _, suffix = c.rpartition(sep)
                if stem:
                    fams.setdefault(stem, []).append((c, suffix))
                break
    return {k: v for k, v in fams.items() if len(v) >= 3}


def _composition_sets(df, numeric_cols, tol=COMP_TOL) -> list:
    """Find (total_col, [part_cols]) where the parts really do sum to the total."""
    out = []
    for total in numeric_cols:
        tv = df[total].astype(float)
        if not (tv > 0).any():
            continue
        # A part can never exceed its own total, so screen on that first. This
        # keeps unrelated numeric columns (population, income, coordinates) out
        # of the candidate set without having to search every subset.
        parts = [c for c in numeric_cols
                 if c != total
                 and (df[c].astype(float) <= tv * (1 + tol) + tol).mean() > 0.99]
        if len(parts) < 2:
            continue
        s = df[parts].astype(float).sum(axis=1)
        ok = np.isclose(s, tv, rtol=tol, atol=max(1e-9, float(tv.abs().median()) * tol))
        if ok.mean() > COMP_HIT_RATE:
            out.append((total, parts))
    return out


def profile(df: pd.DataFrame, name: str = "") -> dict:
    n = len(df)
    kinds = {c: _kind(df[c], c, n) for c in df.columns}

    cols = []
    for c in df.columns:
        s = df[c]
        entry = {"name": c, "kind": kinds[c], "n_missing": int(s.isna().sum()),
                 "n_unique": int(s.nunique(dropna=True))}
        if pd.api.types.is_numeric_dtype(s) and kinds[c] != "identifier":
            v = s.astype(float).dropna()
            if len(v):
                med = float(v.median())
                # Tolerance against float noise: solver output routinely carries
                # values like -1.5e-09 that are structurally zero. Calling those
                # "signed" would wrongly recommend a diverging colour ramp.
                tol = max(abs(float(v.max())), abs(float(v.min()))) * 1e-6
                entry.update(
                    min=float(v.min()), max=float(v.max()), median=med,
                    has_zero=bool((v.abs() <= tol).any()),
                    has_negative=bool((v < -tol).any()),
                    tail_ratio=float(v.max() / med) if med > 0 else None,
                )
        if kinds[c] == "categorical" and entry["n_unique"] <= MAX_NOMINAL:
            vc = s.value_counts()
            entry["groups"] = {str(k): int(x) for k, x in vc.items()}
        cols.append(entry)

    by_kind = {k: [c for c, v in kinds.items() if v == k]
               for k in set(kinds.values())}

    geo = bool(by_kind.get("latitude") and by_kind.get("longitude"))
    numeric = [c["name"] for c in cols if c["kind"] == "continuous"]

    # Repeated measures require an ENTITY that recurs across the levels -- not
    # merely a balanced factor. A between-subjects design (each row a different
    # subject, assigned one treatment) also has balanced level counts, and
    # calling it paired would recommend connecting lines between unrelated
    # observations. So verify that some identifier actually appears under more
    # than one level.
    entity_cands = [c for c in df.columns
                    if kinds[c] in ("identifier", "categorical")
                    and MAX_NOMINAL < df[c].nunique() < n]
    scenarios = []
    for c in by_kind.get("categorical", []):
        nun = df[c].nunique()
        if not (2 <= nun <= 8 and n / max(nun, 1) > 5):
            continue
        counts = df[c].value_counts()
        if counts.std() / max(counts.mean(), 1e-9) >= 0.2:
            continue
        entity = None
        for e in entity_cands:
            if e == c:
                continue
            per_entity = df.groupby(e, observed=True)[c].nunique()
            if (per_entity > 1).mean() > 0.8:
                entity = e
                break
        if entity:
            scenarios.append({"name": c, "entity": entity,
                              "levels": [str(x) for x in counts.index]})

    facets = [{"name": c["name"], "n_levels": c["n_unique"],
               "groups": c.get("groups", {})}
              for c in cols
              if c["kind"] == "categorical" and 2 <= c["n_unique"] <= MAX_NOMINAL]

    wide = _shared_prefix_groups([c for c in numeric])
    comps = _composition_sets(df, numeric) if 3 <= len(numeric) <= 25 else []

    skewed = [c["name"] for c in cols
              if c["kind"] == "continuous" and c.get("tail_ratio")
              and c["tail_ratio"] > SKEW_TAIL_RATIO
              and not c.get("has_negative")]
    # Coordinates are signed by definition; that says nothing about the encoding.
    signed = [c["name"] for c in cols
              if c["kind"] == "continuous" and c.get("has_negative")]

    return {
        "name": name, "n_rows": n, "n_cols": len(df.columns),
        "columns": cols, "by_kind": by_kind,
        "geo": geo, "temporal": by_kind.get("temporal", []),
        "scenarios": scenarios, "facets": facets,
        "wide_families": {k: [s for _, s in v] for k, v in wide.items()},
        "composition_sets": [{"total": t, "parts": p} for t, p in comps],
        "skewed": skewed, "signed": signed,
    }


def available_intents(p: dict) -> list:
    """Which of the nine communicative intents this table can actually express."""
    out = []
    facets = p["facets"]
    numeric = [c for c in p["columns"] if c["kind"] == "continuous"]

    if facets and numeric:
        out.append(("comparison", f"{len(facets)} categorical column(s) x "
                                  f"{len(numeric)} measure(s)"))
        out.append(("distribution", "per-group distributions of any measure; "
                                    "check group sizes before choosing a form"))
    if len(numeric) >= 2:
        out.append(("relationship", f"{len(numeric)} measures can be crossed"))
    if p["temporal"]:
        out.append(("trend", f"temporal column(s): {', '.join(p['temporal'])}"))
    if p["composition_sets"]:
        t = p["composition_sets"][0]
        out.append(("composition", f"{len(t['parts'])} parts sum to {t['total']}"))
    if p["geo"]:
        out.append(("spatial", "latitude/longitude present"))
    if p["scenarios"] or p["wide_families"]:
        out.append(("flow_and_network",
                    "same entities observed under multiple scenarios -- "
                    "category transitions can be traced"))
        out.append(("uncertainty",
                    "repeated measures per entity -- spread can be shown"))
    return out


def decision_points(p: dict) -> list:
    """Emit the choices THIS table leaves open. Not questions -- decision points.

    Deliberately does not phrase questions or invent option wording. Canned
    question text drifts out of sync with the data and reads as boilerplate; the
    agent phrases each one in the user's language using the real column names and
    numbers below. See the skill's Step 2.

    Each entry carries:
      key         stable identifier
      fact        what was measured in THIS table
      forces      the design choice that fact opens up
      settled     None if the user must choose; otherwise the answer the data
                  already determines -- do not ask these, state them

    The `settled` field matters as much as the rest. A profile that leaves ten
    open choices produces an interrogation; most of the ten are usually already
    determined by the data and only need to be reported.
    """
    d = []
    facets = p["facets"]
    numeric = [c for c in p["columns"] if c["kind"] == "continuous"]

    def add(key, fact, forces, settled=None):
        d.append({"key": key, "fact": fact, "forces": forces, "settled": settled})

    if p["geo"]:
        lat = p["by_kind"].get("latitude", ["?"])[0]
        lon = p["by_kind"].get("longitude", ["?"])[0]
        add("map",
            f"coordinate columns present ({lat}, {lon})",
            "whether to spend a panel on location; a map answers where and which "
            "one, and costs the space a second measurement panel would have used")

    for f in facets:
        if f["n_levels"] < 2:
            continue
        sizes = sorted(f["groups"].values())
        span = (f", group n runs {sizes[0]}-{sizes[-1]} (median {sizes[len(sizes)//2]})"
                if sizes else "")
        add(f"split:{f['name']}",
            f"{f['name']} has {f['n_levels']} levels{span}",
            "whether to split on it or pool over it, and -- if the group sizes "
            "above are uneven -- whether to drop the small ones, pool them, or "
            "keep them all. There is no default cutoff: any cutoff changes how "
            "many levels survive and therefore what number the figure states, "
            "so it is a decision to record, not one to inherit")

    if facets and numeric:
        f = min(facets, key=lambda x: min(x["groups"].values()) if x["groups"] else 0)
        sizes = sorted(f["groups"].values()) if f["groups"] else [0]
        add("marks",
            f"smallest {f['name']} group has n = {sizes[0]}, largest n = {sizes[-1]}",
            "how each group is drawn. A fitted density needs enough points to be "
            "credible and the threshold is a judgement call, so decide it against "
            "these counts; showing the observations as well as the summary avoids "
            "the question entirely")

    for c in numeric:
        # A signed quantity cannot go on a log axis, and its max/median ratio is
        # not a meaningful measure of skew, so do not offer the choice.
        if c["name"] in p["skewed"] and c["name"] not in p["signed"]:
            add(f"scale:{c['name']}",
                f"{c['name']} spans {c['tail_ratio']:.0f}x its median "
                f"({c['min']:.4g} to {c['max']:.4g})",
                "log or linear axis; on linear most marks collapse together, on "
                "log the reader compares ratios instead of differences")

    for c in numeric:
        if c["name"] in p["signed"]:
            add(f"zero:{c['name']}",
                f"{c['name']} takes both signs "
                f"({c['min']:.4g} to {c['max']:.4g})",
                "whether zero is a real threshold in this quantity -- if it is, "
                "it needs a reference line and a diverging ramp centred on it")

    for cs in p["composition_sets"]:
        add(f"composition:{cs['total']}",
            f"{len(cs['parts'])} columns verified to sum to {cs['total']}",
            "absolute amounts or shares; level and mix are different claims and "
            "one figure cannot carry both")

    for sc in p["scenarios"]:
        add(f"paired:{sc['name']}",
            f"each {sc['entity']} appears under {len(sc['levels'])} levels of "
            f"{sc['name']} ({', '.join(sc['levels'][:4])}"
            f"{', ...' if len(sc['levels']) > 4 else ''})",
            "paired or independent display",
            settled="the design is paired; averaging across levels would "
                    "discard the pairing, so show change per entity or show "
                    "each level's distribution -- not a single pooled mean")

    for stem, suffixes in p["wide_families"].items():
        add(f"wide:{stem}",
            f"wide-format family {stem}_* ({', '.join(suffixes[:4])})",
            "which of these to show together, and whether as levels or as "
            "differences from a reference level")

    for t in p["temporal"]:
        add(f"time:{t}",
            f"temporal column {t}",
            "the resolution to plot it at; the native resolution is rarely the "
            "right one and aggregating is a decision, not a default")

    return d


def render(p: dict) -> str:
    L = [f"# profile: {p['name'] or 'data'}  ({p['n_rows']} rows x {p['n_cols']} cols)", ""]

    L.append("## columns")
    for c in p["columns"]:
        bits = [f"{c['name']:<34} {c['kind']:<12} uniq={c['n_unique']:<6}"]
        if "median" in c:
            bits.append(f"range=[{c['min']:.4g}, {c['max']:.4g}] med={c['median']:.4g}")
            if c["kind"] == "continuous":
                if c.get("tail_ratio") and c["tail_ratio"] > SKEW_TAIL_RATIO:
                    bits.append(f"tail={c['tail_ratio']:.0f}x")
                if c.get("has_negative"):
                    bits.append("signed")
        if c["n_missing"]:
            bits.append(f"missing={c['n_missing']}")
        L.append("  " + "  ".join(bits))

    if p["facets"]:
        L += ["", "## candidate grouping columns (group sizes, no cutoff applied)"]
        for f in p["facets"]:
            sizes = sorted(f["groups"].values(), reverse=True)
            head = ", ".join(str(x) for x in sizes[:8])
            more = f", ... ({len(sizes)} groups)" if len(sizes) > 8 else ""
            L.append(f"  {f['name']:<34} {f['n_levels']} levels   n = {head}{more}")
        L.append("  -> no threshold is applied here on purpose. Pick one in Step 2")
        L.append("     against these counts and record it with its reason.")

    if p["scenarios"]:
        L += ["", "## repeated-measures structure"]
        for s in p["scenarios"]:
            L.append(f"  {s['name']}: {', '.join(s['levels'])}"
                     f"   (repeated per {s['entity']})")
        L.append("  -> the same entity appears under every level, so the design is")
        L.append("     paired. Averaging across levels discards that pairing.")

    if p["wide_families"]:
        L += ["", "## wide-format scenario families"]
        for stem, suffixes in p["wide_families"].items():
            L.append(f"  {stem}_*: {', '.join(suffixes)}")

    if p["composition_sets"]:
        L += ["", "## composition sets (parts verified to sum to the total)"]
        for cs in p["composition_sets"]:
            L.append(f"  {cs['total']} = " + " + ".join(cs["parts"]))

    if p["skewed"]:
        L += ["", f"## long-tailed measures (max/median > {SKEW_TAIL_RATIO})",
              "  " + ", ".join(p["skewed"])]
    if p["signed"]:
        L += ["", "## measures taking both signs (zero may be a real threshold)",
              "  " + ", ".join(p["signed"])]

    L += ["", "## intents this table can express"]
    for intent, why in available_intents(p):
        L.append(f"  {intent:<18} {why}")

    dp = decision_points(p)
    settled = [d for d in dp if d["settled"]]
    open_ = [d for d in dp if not d["settled"]]

    if settled:
        L += ["", "## settled by the data -- state these, do not ask them"]
        for d in settled:
            L.append(f"  [{d['key']}] {d['fact']}")
            L.append(f"      -> {d['settled']}")

    if open_:
        L += ["", "## open choices -- the user decides these.",
              "## Phrase each in their language using these column names and",
              "## numbers. Do not ask about anything not listed here."]
        for d in open_:
            L.append(f"  [{d['key']}] {d['fact']}")
            L.append(f"      opens: {d['forces']}")
    return "\n".join(L).rstrip()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("path")
    ap.add_argument("--sheet", default=None,
                    help="sheet name; omit to list sheets and profile each")
    ap.add_argument("--max-sheets", type=int, default=6)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    frames = {}
    if a.path.lower().endswith((".xlsx", ".xls", ".xlsm")):
        xl = pd.ExcelFile(a.path)
        names = [a.sheet] if a.sheet else xl.sheet_names
        if not a.sheet and len(names) > a.max_sheets:
            print(f"{len(names)} sheets: {', '.join(names)}")
            print(f"\nprofiling the first {a.max_sheets}; "
                  f"use --sheet NAME for the others\n")
            names = names[:a.max_sheets]
        for s in names:
            frames[s] = pd.read_excel(a.path, sheet_name=s)
    else:
        frames[a.path] = pd.read_csv(a.path)

    profiles = []
    for name, df in frames.items():
        p = profile(df, name)
        p["decision_points"] = decision_points(p)
        profiles.append(p)
        print(render(p))
        print()

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, default=str)
        print(f"wrote {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
