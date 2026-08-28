"""
nature_panels.py -- the recurring data-panel families, drawn to house style.

`nature_style` sets the type and the axes. `nature_map`, `nature_quadrant` and
`nature_chord.R` handle the three families whose *geometry* defeats a generic
styling pass. This module covers the rest: the panels that appear in almost
every quantitative paper -- distributions, coefficients, compositions, fits,
joint densities, state timelines, matrices -- where the trap is not geometry
but a handful of decisions that are easy to get subtly wrong and hard to see
afterwards.

Usage
-----
    from nature_style import panel, apply_style, clean_axes, save_all
    from nature_panels import violin_box, forest, stacked_bars, fit_line

    p = panel(placed_mm=60, aspect=0.8)
    apply_style(p)
    fig, ax = plt.subplots(figsize=p.figsize)
    violin_box(ax, [group_a, group_b, group_c], spec=p)
    clean_axes(ax)
    save_all("fig3_a_distribution", fig)

Design rules encoded here
-------------------------
* **Uncertainty is drawn, or its absence is stated.** Every function that shows
  a summary (a mean, a median, a coefficient) either takes an interval or
  reports `n` -- a bare summary with no spread is the most common way a panel
  overstates what the data supports.
* **Intervals beat stars.** `forest` colours by whether an interval excludes
  the reference value, not by a p-value threshold, and nothing in this module
  draws significance asterisks. See `references/panels.md` §4.
* **Order is a decision, not a default.** Anything that draws categories takes
  an explicit order and keeps it across panels, because a grid whose rows are
  each sorted independently cannot be read across.
* **Data-derived annotations belong in the script; everything else does not.**
  `stat_box` exists because R^2 and n move when the data moves. Callouts,
  arrows and prose do not, and are added at assembly (SKILL.md Step 4).
* Geometry scales with `spec` exactly as in the other modules, so a panel
  shrunk at assembly keeps its intended weight.

Depends on numpy and matplotlib only. scipy is used when present (kernel
density, exact p-values) and cleanly skipped when it is not.

Self-test: `python nature_panels.py` renders one demo panel per family from
synthetic data.
"""

from __future__ import annotations

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

__all__ = [
    # shared helpers
    "auto_unit", "headroom", "stat_box", "ragged_grid", "tidy_grid",
    # panel families
    "violin_box", "forest", "stacked_bars", "grouped_bars", "fit_line",
    "density_field", "runs", "state_bands", "matrix_panel",
]


def _scale_of(spec) -> float:
    """Draw scale carried by a Panel, or 1.0 when drawing unscaled."""
    return getattr(spec, "draw_scale", 1.0) if spec is not None else 1.0


def _finite(a):
    a = np.asarray(a, dtype=float)
    return a[np.isfinite(a)]


def _slot_fits(ax, n_slots: int, longest: str, axis: str = "x",
               fill: float = 0.9) -> bool:
    """Would `longest` fit inside one of `n_slots` slots across `axis`?

    Cheap approximation -- Arial averages about 0.55 em per character -- but
    cheap and roughly right beats the alternative, which is discovering the
    overlap in the assembled PDF. Used to decide whether an optional text
    layer can be added at all, never to silently shrink type below house size.
    """
    try:
        box = ax.get_window_extent()
        extent_in = (box.width if axis == "x" else box.height) / ax.figure.dpi
    except Exception:
        return True
    slot_pt = (extent_in * 72.0) / max(n_slots, 1)
    key = "xtick.labelsize" if axis == "x" else "ytick.labelsize"
    need_pt = 0.55 * len(longest) * _pt(mpl.rcParams[key])
    return need_pt <= slot_pt * fill


def _pt(size) -> float:
    """Font size in points, resolving matplotlib's relative names ('medium')."""
    if isinstance(size, (int, float)):
        return float(size)
    from matplotlib.font_manager import FontProperties
    return float(FontProperties(size=size).get_size_in_points())


# --------------------------------------------------------------------------
# Shared helpers
#
# Small, boring, and responsible for a large share of the difference between
# a panel that reads and one that does not.
# --------------------------------------------------------------------------


#: Multipliers that keep tick numbers inside style.md's 0.1-999 window.
_UNIT_STEPS = [
    (1e-9, "n"), (1e-6, "u"), (1e-3, "m"), (1.0, ""),
    (1e3, "k"), (1e6, "M"), (1e9, "G"), (1e12, "T"),
]


def auto_unit(values, unit: str = "", prefer=None):
    """Rescale a series so its tick labels land in 0.1-999.

    Returns ``(scaled_values, label_unit, divisor)``. The house rule
    (style.md §4) is that a unit change always beats scientific notation:
    `Power (kW)` reads, `Power (W) x10^3` does not.

        y, u, _ = auto_unit(watts, "W")
        ax.plot(t, y)
        ax.set_ylabel(f"Power ({u})")

    `prefer` pins the divisor when several panels must share one unit -- pass
    the divisor returned for the largest panel, or the tick labels will agree
    with the axis label in one panel and disagree in the next.
    """
    v = _finite(values)
    if prefer is not None:
        div = float(prefer)
    elif v.size == 0:
        div = 1.0
    else:
        peak = np.nanmax(np.abs(v))
        div = 1.0
        if peak > 0:
            for mult, _ in _UNIT_STEPS:
                if peak / mult >= 1.0:
                    div = mult
    prefix = dict(_UNIT_STEPS).get(div, "")
    return np.asarray(values, dtype=float) / div, f"{prefix}{unit}", div


def headroom(ax, values=None, frac: float = 0.12, axis: str = "y",
             floor_zero: bool = True):
    """Leave room above the data for value labels, stars, or a legend.

    Matplotlib's autoscale fits the marks, not the annotations that sit on
    top of them, so bar-top labels collide with the spine on roughly every
    first draft. `floor_zero` pins the baseline at zero, which a bar chart
    always requires and a line chart of a non-negative quantity usually wants.
    """
    if values is None:
        lo, hi = ax.get_ylim() if axis == "y" else ax.get_xlim()
    else:
        v = _finite(values)
        lo, hi = (0.0, 1.0) if v.size == 0 else (float(v.min()), float(v.max()))
    if floor_zero and lo > 0:
        lo = 0.0
    span = hi - lo
    if span <= 0:
        span = abs(hi) or 1.0
    setter = ax.set_ylim if axis == "y" else ax.set_xlim
    setter(lo, hi + span * frac)
    return ax


def stat_box(ax, spec=None, loc: str = "upper left", color: str = None,
             fontsize: float = None, **stats):
    """Annotate the data-derived statistics a reader would otherwise ask for.

        stat_box(ax, r2=0.62, p=2e-5, n=418)      -> R^2 = 0.62 / P < 0.001 / n = 418

    These are legitimate in-script text (SKILL.md Step 4) precisely because
    they are functions of the data: re-run the analysis and they must move.
    Prose, callouts and arrows are not, and belong at assembly.

    P values are formatted with the `P < 0.001` floor rather than printed to
    six decimals, because below that threshold the digits are noise. Pass any
    other keyword to add a line: `stat_box(ax, n=90, slope=1.4)`.
    """
    s = _scale_of(spec)
    lines = []
    if "r2" in stats:
        lines.append(rf"$R^2 = {stats.pop('r2'):.2f}$")
    if "r" in stats:
        lines.append(rf"$r = {stats.pop('r'):.2f}$")
    if "p" in stats:
        p = stats.pop("p")
        lines.append(r"$P < 0.001$" if p < 1e-3 else rf"$P = {p:.3f}$")
    if "n" in stats:
        lines.append(rf"$n = {int(stats.pop('n')):,}$")
    for key, val in stats.items():
        val = f"{val:.3g}" if isinstance(val, (int, float)) else val
        lines.append(rf"{key} = {val}")
    if not lines:
        return ax

    corners = {
        "upper left": (0.04, 0.96, "left", "top"),
        "upper right": (0.96, 0.96, "right", "top"),
        "lower left": (0.04, 0.04, "left", "bottom"),
        "lower right": (0.96, 0.04, "right", "bottom"),
    }
    if loc not in corners:
        raise ValueError(f"loc must be one of {sorted(corners)}, got {loc!r}")
    x, y, ha, va = corners[loc]
    if fontsize is None:
        fontsize = mpl.rcParams["font.size"]
    ax.text(x, y, "\n".join(lines), transform=ax.transAxes,
            fontsize=fontsize, ha=ha, va=va, linespacing=1.35,
            color=color or mpl.rcParams["text.color"], zorder=6)
    return ax


def ragged_grid(fig, n: int, n_cols: int, **kw):
    """A subplot grid for `n` panels, with the trailing slots removed.

    Returns ``(axes_used, n_rows)``. Unused slots are made invisible rather
    than left as empty framed boxes, which is what `plt.subplots` gives you
    and what ships in a surprising number of supplements.
    """
    n_rows = int(np.ceil(n / n_cols))
    axes = fig.subplots(n_rows, n_cols, **kw)
    flat = np.atleast_1d(axes).ravel()
    for k in range(n, flat.size):
        flat[k].set_visible(False)
    return list(flat[:n]), n_rows


def tidy_grid(axes, n_cols: int, xlabel: str = None, ylabel: str = None,
              keep_xticks: bool = True):
    """Keep axis labels on the outer ring of a possibly *ragged* grid.

    `nature_style.share_outer_labels` assumes a full rectangle. When the last
    row is short, the bottom-most panel of each column is not in the last row,
    and blanking its tick labels leaves a column of panels with no x axis at
    all. The test is `i + n_cols >= n`, not `row == n_rows - 1`.
    """
    axes = list(axes)
    n = len(axes)
    for i, ax in enumerate(axes):
        col = i % n_cols
        is_bottom = (i + n_cols) >= n
        if col > 0:
            ax.set_ylabel("")
            ax.tick_params(labelleft=False)
        elif ylabel:
            ax.set_ylabel(ylabel)
        if not is_bottom:
            ax.set_xlabel("")
            if keep_xticks:
                ax.tick_params(labelbottom=False)
        elif xlabel:
            ax.set_xlabel(xlabel)
    return axes


# --------------------------------------------------------------------------
# Distributions
#
# A violin is a density estimate, and a density estimate is a model. The two
# things a reader needs in order to discount it -- the sample size and the
# actual quartiles -- are exactly what the default rendering hides.
# --------------------------------------------------------------------------


def violin_box(ax, data, positions=None, colors=None, spec=None, labels=None,
               widths: float = 0.85, box_width: float = 0.18,
               whisker: float = 1.5, show_n: bool = False,
               edge: str = "black", alpha: float = 0.85):
    """Violin with a real box-and-whisker drawn inside it.

    Returns the list of per-group summary dicts (n, median, q1, q3, whisker
    ends), so the caption can quote numbers that came from the same code that
    drew them.

    Three deliberate departures from `ax.violinplot` defaults:

    1. `showextrema` is off and the whiskers are redrawn at Tukey 1.5 x IQR.
       Matplotlib's default extrema bars run to the data minimum and maximum,
       so their length is a function of sample size rather than of spread --
       two groups with identical distributions get visibly different violins
       purely because one has more points.
    2. The IQR box is drawn in **white on top of the body**, not as a coloured
       overlay. Colour is already carrying the group; a second colour inside
       the violin makes the reader look for a second variable.
    3. The median is a separate, heavier tick rather than a thin line, because
       it is the one number most captions actually quote.

    `show_n=True` folds the group sizes into the tick labels (pass `labels`
    for the category names). Use it whenever the groups are unbalanced -- a
    fat violin over n = 6 is the single most misleading mark in common use.
    The sizes go in the tick labels rather than as free-floating text so that
    matplotlib spaces them on the same rules as the categories; annotations
    placed by hand under each violin collide as soon as the panel is narrow.
    """
    s = _scale_of(spec)
    groups = [_finite(d) for d in data]
    if positions is None:
        positions = np.arange(1, len(groups) + 1)
    positions = np.asarray(positions, dtype=float)

    non_empty = [i for i, g in enumerate(groups) if g.size > 0]
    if non_empty:
        parts = ax.violinplot([groups[i] for i in non_empty],
                              positions=positions[non_empty],
                              widths=widths, showmeans=False,
                              showmedians=False, showextrema=False)
        for k, body in zip(non_empty, parts["bodies"]):
            if colors is not None:
                body.set_facecolor(colors[k % len(colors)])
            body.set_edgecolor(edge)
            body.set_linewidth(0.8 * s)
            body.set_alpha(alpha)

    summaries = []
    for i, g in enumerate(groups):
        if g.size == 0:
            summaries.append(dict(n=0, median=np.nan, q1=np.nan, q3=np.nan,
                                  lo=np.nan, hi=np.nan))
            continue
        q1, med, q3 = np.percentile(g, [25, 50, 75])
        iqr = q3 - q1
        lo = max(g.min(), q1 - whisker * iqr)
        hi = min(g.max(), q3 + whisker * iqr)
        pos = positions[i]

        ax.vlines(pos, lo, hi, color=edge, lw=0.8 * s, zorder=2)
        ax.add_patch(mpl.patches.Rectangle(
            (pos - box_width / 2, q1), box_width, q3 - q1,
            facecolor="white", edgecolor=edge, linewidth=0.8 * s, zorder=3))
        ax.hlines(med, pos - box_width / 2, pos + box_width / 2,
                  color=edge, lw=1.2 * s, zorder=4)
        summaries.append(dict(n=int(g.size), median=float(med), q1=float(q1),
                              q3=float(q3), lo=float(lo), hi=float(hi)))

    ax.set_xticks(positions)
    if labels is not None or show_n:
        base = list(labels) if labels is not None else [""] * len(groups)
        if show_n:
            # Bare digits, not "n = 300" and not "(300)": both prefixes double
            # or triple the label width. Then measure -- overlapping counts are
            # worse than absent ones, and a panel this narrow needs the sizes
            # in the caption instead. The caption says the second line is n.
            counts = [f"{sm['n']}" for sm in summaries]
            widest = max(counts, key=len)
            if _slot_fits(ax, len(groups), widest):
                base = [f"{t}\n{c}" if t else c for t, c in zip(base, counts)]
            else:
                import warnings
                warnings.warn(
                    f"violin_box: {len(groups)} group sizes do not fit across "
                    f"this panel; showing categories only. Widen the panel or "
                    f"report n in the caption.", stacklevel=2)
        ax.set_xticklabels(base)
    return summaries


# --------------------------------------------------------------------------
# Coefficients
# --------------------------------------------------------------------------


def forest(ax, labels, estimate, lo, hi, spec=None, order=None,
           reference: float = 0.0, kind: str = "point",
           color_excl: str = "#982B2D", color_incl: str = "#0B75B3",
           hatch=None, height: float = 0.62, capsize: float = None,
           sort: bool = False):
    """Coefficient / effect-size panel: estimates with intervals, against a line.

    `lo` and `hi` are the interval **bounds**, not the distances from the
    estimate. This module converts them, because `xerr` wants distances and
    passing bounds straight in is the most common silent error in this chart:
    the bars still render, they are just wrong, and asymmetric intervals hide
    it well.

    `kind='point'` draws a dot-and-whisker (the forest-plot convention, and
    the right default when the estimates are effects). `kind='bar'` draws
    horizontal bars, which suit standardised regression coefficients where the
    reader is comparing magnitudes.

    **Colour encodes whether the interval excludes the reference**, not a
    p-value threshold. It is the same information when the interval is a 95%
    CI, but it stays honest under bootstrap and cluster-robust intervals,
    where a naive p-value is inflated by pseudo-replication. Nothing here
    draws asterisks -- see references/panels.md §4.

    `order` fixes the row order. Pass the *same* order to every panel of a
    grid: a six-panel figure whose rows are each sorted by their own effect
    size cannot be read across, which is the only reason to draw six panels.
    `sort=True` orders by estimate and is for a single standalone panel.
    """
    s = _scale_of(spec)
    labels = list(labels)
    est = np.asarray(estimate, dtype=float)
    lo = np.asarray(lo, dtype=float)
    hi = np.asarray(hi, dtype=float)
    if not (len(labels) == est.size == lo.size == hi.size):
        raise ValueError("labels, estimate, lo and hi must be the same length")
    if np.any(lo > hi):
        raise ValueError("lo must not exceed hi -- pass interval bounds, "
                         "not error distances")

    if order is not None:
        idx = [labels.index(k) for k in order]
    elif sort:
        idx = list(np.argsort(est))
    else:
        idx = list(range(len(labels)))
    labels = [labels[i] for i in idx]
    est, lo, hi = est[idx], lo[idx], hi[idx]

    excludes = (lo > reference) | (hi < reference)
    colors = [color_excl if e else color_incl for e in excludes]
    y = np.arange(len(labels))

    # xerr wants distances from the estimate, in a (2, n) array.
    err = np.vstack([est - lo, hi - est])
    err[err < 0] = 0.0

    if capsize is None:
        capsize = 2.0 * s
    if kind == "bar":
        for i in range(len(y)):
            ax.barh(y[i], est[i], height=height,
                    xerr=err[:, i:i + 1], color=colors[i],
                    hatch=None if hatch is None else hatch[idx[i]],
                    edgecolor="white", linewidth=0.3 * s,
                    error_kw=dict(ecolor="#333333", elinewidth=0.8 * s,
                                  capsize=capsize, capthick=0.8 * s),
                    zorder=3)
    elif kind == "point":
        for i in range(len(y)):
            ax.errorbar(est[i], y[i], xerr=err[:, i:i + 1], fmt="o",
                        color=colors[i], markersize=3.4 * s,
                        elinewidth=0.9 * s, capsize=capsize,
                        capthick=0.9 * s, zorder=3)
    else:
        raise ValueError("kind must be 'point' or 'bar'")

    ax.axvline(reference, color="#333333", lw=0.8 * s, ls="-", zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_ylim(y[0] - 0.7, y[-1] + 0.7)
    ax.invert_yaxis()          # first row at the top, reading order
    return dict(labels=labels, estimate=est, lo=lo, hi=hi,
                excludes_reference=excludes)


# --------------------------------------------------------------------------
# Compositions
#
# A stacked bar answers "what is this made of". It answers "how big is it"
# badly, and "how did the third component change" worse -- only the bottom
# segment sits on a common baseline. Both weaknesses have a fix that costs
# one extra mark.
# --------------------------------------------------------------------------


def stacked_bars(ax, x, components, colors=None, labels=None, spec=None,
                 width: float = 0.7, total: bool = True,
                 total_color: str = "#000000", value_labels=None,
                 signed: bool = False):
    """Stacked bars, with the total drawn as its own mark.

    `components` is a (n_groups, n_components) array, or a dict mapping
    component name -> per-group values, in which case the dict order is the
    stacking order and supplies the labels.

    **`total=True` is the point of this function.** In a stacked bar the total
    exists only as the top edge of the stack, and an edge at a different
    height in every group is something the eye compares badly -- which is why
    "the total barely moved" is so often invisible in a chart that shows it.
    Drawing the total as an explicit line-and-marker layer puts it on a common
    baseline without giving up the composition.

    `signed=True` stacks positive components upward from zero and negative
    ones downward, so a cost/benefit or source/sink panel keeps zero as a real
    baseline. The total line is then the net, which is the number the panel is
    usually about and which no segment shows.

    Returns the per-group totals.
    """
    s = _scale_of(spec)
    if isinstance(components, dict):
        labels = list(components.keys()) if labels is None else labels
        comp = np.column_stack([np.asarray(v, dtype=float)
                                for v in components.values()])
    else:
        comp = np.asarray(components, dtype=float)
    x = np.asarray(x, dtype=float)
    if comp.shape[0] != x.size:
        raise ValueError(f"components has {comp.shape[0]} rows but x has "
                         f"{x.size} entries -- expected one row per group")

    n_comp = comp.shape[1]
    if colors is None:
        cycle = mpl.rcParams["axes.prop_cycle"].by_key().get("color", [])
        colors = [cycle[j % len(cycle)] for j in range(n_comp)] if cycle else None

    pos_base = np.zeros(x.size)
    neg_base = np.zeros(x.size)
    for j in range(n_comp):
        vals = comp[:, j]
        if signed:
            up = np.where(vals > 0, vals, 0.0)
            down = np.where(vals < 0, vals, 0.0)
            ax.bar(x, up, bottom=pos_base, width=width,
                   color=None if colors is None else colors[j],
                   edgecolor="white", linewidth=0.3 * s, zorder=2,
                   label=None if labels is None else labels[j])
            ax.bar(x, down, bottom=neg_base, width=width,
                   color=None if colors is None else colors[j],
                   edgecolor="white", linewidth=0.3 * s, zorder=2)
            pos_base += up
            neg_base += down
        else:
            if np.any(vals < 0):
                raise ValueError(
                    "negative values in an unsigned stack -- segments would "
                    "overlap and the top edge would stop being the total; "
                    "pass signed=True")
            ax.bar(x, vals, bottom=pos_base, width=width,
                   color=None if colors is None else colors[j],
                   edgecolor="white", linewidth=0.3 * s, zorder=2,
                   label=None if labels is None else labels[j])
            pos_base += vals

    totals = comp.sum(axis=1)
    if total:
        ax.plot(x, totals, color=total_color, lw=1.4 * s, marker="o",
                markersize=3.5 * s, markerfacecolor=total_color,
                markeredgecolor=total_color, zorder=4,
                label="Total" if labels is not None else None)
    if signed:
        ax.axhline(0, color="#333333", lw=0.8 * s, zorder=3)

    if value_labels is not None:
        span = float(np.nanmax(np.abs(totals))) or 1.0
        for xi, tot in zip(x, totals):
            txt = value_labels(tot) if callable(value_labels) else f"{tot:.4g}"
            ax.annotate(txt, (xi, tot), xytext=(0, 4 * s),
                        textcoords="offset points", ha="center",
                        va="bottom" if tot >= 0 else "top",
                        fontsize=mpl.rcParams["xtick.labelsize"], zorder=5)
        headroom(ax, np.r_[totals, neg_base], frac=0.18,
                 floor_zero=not signed)
    ax.set_xticks(x)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4))
    return totals


def grouped_bars(ax, x, series, colors=None, labels=None, spec=None,
                 ci=None, group_width: float = 0.8, edge: str = "white"):
    """Side-by-side bars for a few series, with intervals rather than stars.

    `series` is (n_groups, n_series) or a dict of name -> values. `ci`, when
    given, is a (n_groups, n_series, 2) array of interval **bounds** in the
    same layout, converted to distances here for the same reason as `forest`.

    The dodge arithmetic is the part people rewrite each time and get slightly
    wrong: bar width is `group_width / n_series`, and offsets are centred on
    the tick, so the group stays visually attached to its own label rather
    than drifting right as series are added.

    Deliberately absent: significance asterisks. A star encodes a threshold
    crossing and hides the effect size, and readers consistently read three
    stars as "three times as important". Show the interval.
    """
    s = _scale_of(spec)
    if isinstance(series, dict):
        labels = list(series.keys()) if labels is None else labels
        vals = np.column_stack([np.asarray(v, dtype=float)
                                for v in series.values()])
    else:
        vals = np.asarray(series, dtype=float)
    x = np.asarray(x, dtype=float)
    n_series = vals.shape[1]
    w = group_width / n_series
    offsets = (np.arange(n_series) - (n_series - 1) / 2) * w

    if ci is not None:
        ci = np.asarray(ci, dtype=float)
        if ci.shape != (vals.shape[0], n_series, 2):
            raise ValueError("ci must have shape (n_groups, n_series, 2) of "
                             "interval bounds")

    for j in range(n_series):
        err = None
        if ci is not None:
            err = np.vstack([vals[:, j] - ci[:, j, 0], ci[:, j, 1] - vals[:, j]])
            err[err < 0] = 0.0
        ax.bar(x + offsets[j], vals[:, j], width=w,
               color=None if colors is None else colors[j % len(colors)],
               edgecolor=edge, linewidth=0.3 * s, zorder=3,
               label=None if labels is None else labels[j],
               yerr=err,
               error_kw=dict(ecolor="#333333", elinewidth=0.8 * s,
                             capsize=2.0 * s, capthick=0.8 * s))
    ax.set_xticks(x)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4))
    return offsets


# --------------------------------------------------------------------------
# Relationships
# --------------------------------------------------------------------------


def _t_crit(dof: float, level: float = 0.95) -> float:
    """Two-sided t critical value; normal approximation without scipy."""
    try:
        from scipy import stats
    except ImportError:
        return 1.959963985 if level == 0.95 else 2.575829
    return float(stats.t.ppf(0.5 + level / 2, dof))


def _t_sf(t: float, dof: float) -> float:
    try:
        from scipy import stats
    except ImportError:
        # Normal tail, adequate for the "is it < 0.001" question a panel asks.
        return float(np.exp(-0.5 * t * t) / (abs(t) + 1e-12) / np.sqrt(2 * np.pi) * 2)
    return float(2 * stats.t.sf(abs(t), dof))


def fit_line(ax, x, y, spec=None, level: float = 0.95, color: str = "#d2352c",
             band: str = None, scatter: bool = True, point_color: str = "#3C5488",
             alpha: float = 0.3, size: float = None, extend: bool = False,
             rasterize_above: int = 5000, annotate: str = "upper left"):
    """Scatter with an OLS fit and a confidence band on the fitted line.

    Returns ``dict(slope, intercept, r2, p, n, se_slope)``.

    Three things this gets right that a hand-rolled version usually does not:

    * **The band is not extrapolated.** It is drawn across the observed range
      of x only. A ribbon that continues past the data is a claim about a
      region where there is none, and it is the part of the panel a reviewer
      reads first.
    * **The band is the interval on the fitted line** (mean response), which
      narrows at the centroid and flares at the ends. A constant-width ribbon
      is a different, wrong object; a prediction interval is a third one, and
      the caption has to say which is drawn.
    * **Dense scatters rasterise** above `rasterize_above` points, so the
      panel stays vector where it matters (axes, text, the fit) and the PDF
      stays under the 50 MB submission cap.

    `annotate` places the R^2 / P / n box; pass None to suppress it.
    """
    s = _scale_of(spec)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    n = x.size
    if n < 3:
        raise ValueError(f"need at least 3 finite pairs to fit, got {n}")

    xbar, ybar = x.mean(), y.mean()
    sxx = float(((x - xbar) ** 2).sum())
    if sxx == 0:
        raise ValueError("x has zero variance -- no line to fit")
    slope = float(((x - xbar) * (y - ybar)).sum() / sxx)
    intercept = float(ybar - slope * xbar)
    resid = y - (intercept + slope * x)
    dof = n - 2
    sigma2 = float((resid ** 2).sum() / dof)
    se_slope = float(np.sqrt(sigma2 / sxx))
    sst = float(((y - ybar) ** 2).sum())
    r2 = float(1 - (resid ** 2).sum() / sst) if sst > 0 else np.nan
    p = _t_sf(slope / se_slope, dof) if se_slope > 0 else 0.0

    if scatter:
        if size is None:
            size = 12 * s ** 2
        ax.scatter(x, y, s=size, color=point_color, alpha=alpha,
                   linewidths=0, zorder=2,
                   rasterized=n > rasterize_above)

    lo_x, hi_x = (ax.get_xlim() if extend else (x.min(), x.max()))
    grid = np.linspace(lo_x, hi_x, 200)
    fitted = intercept + slope * grid
    se_fit = np.sqrt(sigma2 * (1.0 / n + (grid - xbar) ** 2 / sxx))
    half = _t_crit(dof, level) * se_fit

    ax.fill_between(grid, fitted - half, fitted + half,
                    color=band or color, alpha=0.18, linewidth=0, zorder=3)
    ax.plot(grid, fitted, color=color, lw=1.5 * s, zorder=4)

    stats_out = dict(slope=slope, intercept=intercept, r2=r2, p=p, n=n,
                     se_slope=se_slope)
    if annotate:
        stat_box(ax, spec=spec, loc=annotate, r2=r2, p=p, n=n)
    return stats_out


def _smooth2d(field, sigma: float):
    """Separable Gaussian blur in pure numpy (scipy not required)."""
    if sigma <= 0:
        return field
    radius = max(1, int(round(3 * sigma)))
    t = np.arange(-radius, radius + 1)
    k = np.exp(-0.5 * (t / sigma) ** 2)
    k /= k.sum()
    out = np.apply_along_axis(
        lambda m: np.convolve(np.pad(m, radius, mode="edge"), k, mode="valid"),
        0, field.astype(float))
    out = np.apply_along_axis(
        lambda m: np.convolve(np.pad(m, radius, mode="edge"), k, mode="valid"),
        1, out)
    return out


def density_field(ax, x, y, spec=None, bins: int = 60, smooth: float = 1.5,
                  cmap="Blues", log: bool = False, clip=(0, 99),
                  fill_background: bool = True, levels: int = None):
    """A 2D density surface, for the scatter that has too many points to be one.

    Returns ``(mesh, counts, extent)``.

    `clip` is a pair of percentiles applied to **x and y**, not to the colour
    scale: one long tail otherwise buys itself 80% of the panel and leaves the
    mass of the data compressed into a corner. The default drops the top 1% of
    each axis. State it in the caption -- clipping data out of a panel is a
    reportable choice, and `stat_box(..., n=...)` should quote the plotted n.

    `log=True` switches the colour scale to `LogNorm`, which is the right
    default for counts with a long tail (style.md §13) and turns "one bright
    cell and a black field" back into readable structure.

    `fill_background=True` paints the axes the colormap's zero colour, so
    empty regions and near-empty regions are continuous. Left white, a density
    panel grows a halo along its own support boundary that reads as a feature.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if clip is not None:
        xlo, xhi = np.percentile(x, clip)
        ylo, yhi = np.percentile(y, clip)
        keep = (x >= xlo) & (x <= xhi) & (y >= ylo) & (y <= yhi)
        x, y = x[keep], y[keep]
    counts, xe, ye = np.histogram2d(x, y, bins=bins)
    field = _smooth2d(counts, smooth)

    cmap_obj = plt.get_cmap(cmap)
    if fill_background:
        ax.set_facecolor(cmap_obj(0.0))

    norm = None
    if log:
        floor = field[field > 0].min() if np.any(field > 0) else 1.0
        norm = mpl.colors.LogNorm(vmin=floor, vmax=max(field.max(), floor * 10))
        field = np.where(field > 0, field, floor)

    extent = (xe[0], xe[-1], ye[0], ye[-1])
    if levels:
        xc = 0.5 * (xe[:-1] + xe[1:])
        yc = 0.5 * (ye[:-1] + ye[1:])
        mesh = ax.contourf(xc, yc, field.T, levels=levels, cmap=cmap_obj,
                           norm=norm, zorder=1)
    else:
        mesh = ax.pcolormesh(xe, ye, field.T, cmap=cmap_obj, norm=norm,
                             shading="auto", zorder=1, rasterized=True)
    ax.set_xlim(xe[0], xe[-1])
    ax.set_ylim(ye[0], ye[-1])
    return mesh, counts, extent


# --------------------------------------------------------------------------
# State over time
#
# A time series whose interpretation depends on a regime -- day/night,
# charging/discharging, peak/off-peak, treated/untreated -- needs the regime
# drawn, not described in the caption. The regime is background; the series
# is foreground; the zorder ladder is what keeps it that way.
# --------------------------------------------------------------------------


def runs(mask, index=None, min_length: int = 1):
    """Convert a boolean series into the (start, end) spans where it is True.

    Returns a list of ``(start, end)`` pairs in the units of `index`
    (positions when `index` is None). This is the loop that everyone rewrites
    per figure and that gets the last span wrong: a run still open at the end
    of the series has to be closed explicitly, or the final -- usually the
    most interesting -- band silently disappears.

    `min_length` drops runs shorter than n samples, for state columns that
    flicker at the sampling rate.
    """
    m = np.asarray(mask).astype(bool)
    if index is None:
        index = np.arange(m.size)
    index = np.asarray(index)
    if index.size != m.size:
        raise ValueError("mask and index must be the same length")
    if m.size == 0:
        return []

    edges = np.diff(m.astype(np.int8))
    starts = list(np.flatnonzero(edges == 1) + 1)
    ends = list(np.flatnonzero(edges == -1))
    if m[0]:
        starts.insert(0, 0)
    if m[-1]:
        ends.append(m.size - 1)           # close the run left open at the end
    return [(index[a], index[b]) for a, b in zip(starts, ends)
            if (b - a + 1) >= min_length]


def state_bands(ax, spans, color: str, label: str = None, alpha: float = 0.25,
                zorder: int = 1, orient: str = "x"):
    """Shade a list of (start, end) spans as a background regime.

    Only the first span carries the label, so a regime that occurs eleven
    times contributes one legend entry rather than eleven. That single line is
    the difference between a usable legend and an unusable one, and it is the
    detail most often missed.

    Keep the zorder ladder explicit and in this order: bands 1-2, grid 3,
    data 4+. Matplotlib will otherwise draw a 25%-alpha rectangle over the
    line the panel is about.
    """
    span_fn = ax.axvspan if orient == "x" else ax.axhspan
    first = True
    for start, end in spans:
        span_fn(start, end, color=color, alpha=alpha, zorder=zorder,
                linewidth=0, label=label if (first and label) else None)
        first = False
    return ax


# --------------------------------------------------------------------------
# Matrices
# --------------------------------------------------------------------------


def matrix_panel(ax, M, labels=None, spec=None, cmap="RdBu_r",
                 vcenter: float = 0.0, vlim=None, triangle: str = None,
                 annotate=None, grid_color: str = "white",
                 fmt: str = "{:.2f}"):
    """Correlation / confusion / transition matrix as a heatmap.

    Returns the mesh, for a colorbar.

    * **The colour scale is centred, not stretched to the data.** A
      correlation matrix drawn with `Normalize` over the observed range puts
      the neutral colour at whatever the mean correlation happens to be, so
      the same matrix changes sign-appearance when a variable is added.
      `vcenter` pins it; pass `vcenter=None` for a sequential quantity such as
      a confusion count.
    * **`triangle='lower'` masks the redundant half** of a symmetric matrix.
      Drawing both halves spends half the panel restating the other half, and
      makes the diagonal harder to find.
    * **`annotate` prints the numbers only when they fit.** The default prints
      them up to 6x6 and suppresses them above that, and it measures the cell
      against the rendered text rather than trusting the count -- a 6x6 matrix
      in a 40 mm inset has no room for `-0.42` either. When the numbers are
      dropped the colour still carries the value and the colorbar reads it;
      when they matter more than the pattern, the answer is a table.
      Pass True or False to override the measurement.
    """
    s = _scale_of(spec)
    M = np.asarray(M, dtype=float)
    if M.ndim != 2:
        raise ValueError("M must be 2-D")
    n_r, n_c = M.shape
    D = M.copy()

    if triangle in ("lower", "upper"):
        if n_r != n_c:
            raise ValueError("triangle masking needs a square matrix")
        keep = np.tril(np.ones_like(D, dtype=bool)) if triangle == "lower" \
            else np.triu(np.ones_like(D, dtype=bool))
        D = np.where(keep, D, np.nan)
    elif triangle is not None:
        raise ValueError("triangle must be 'lower', 'upper' or None")

    finite = D[np.isfinite(D)]
    if vlim is not None:
        vmin, vmax = vlim
    elif vcenter is not None:
        reach = float(np.nanmax(np.abs(finite - vcenter))) if finite.size else 1.0
        vmin, vmax = vcenter - reach, vcenter + reach
    else:
        vmin, vmax = (float(finite.min()), float(finite.max())) if finite.size else (0.0, 1.0)

    mesh = ax.pcolormesh(np.ma.masked_invalid(D), cmap=cmap, vmin=vmin,
                         vmax=vmax, edgecolors=grid_color,
                         linewidth=0.4 * s, shading="flat")
    ax.set_aspect("equal")
    ax.invert_yaxis()                       # row 0 at the top, like the table
    ax.set_xticks(np.arange(n_c) + 0.5)
    ax.set_yticks(np.arange(n_r) + 0.5)
    if labels is not None:
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticklabels(labels)
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)

    if annotate is None:
        widest = max(fmt.format(vmin), fmt.format(vmax), key=len)
        annotate = max(n_r, n_c) <= 6 and _slot_fits(ax, n_c, widest)
    if annotate:
        norm = mpl.colors.Normalize(vmin, vmax)
        cmap_obj = plt.get_cmap(cmap)
        for i in range(n_r):
            for j in range(n_c):
                if not np.isfinite(D[i, j]):
                    continue
                rgba = cmap_obj(norm(D[i, j]))
                lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
                ax.text(j + 0.5, i + 0.5, fmt.format(D[i, j]),
                        ha="center", va="center",
                        color="white" if lum < 0.5 else "#222222",
                        fontsize=mpl.rcParams["xtick.labelsize"])
    return mesh


# --------------------------------------------------------------------------
# Self-test: one demo panel per family, on synthetic data.
# --------------------------------------------------------------------------

if __name__ == "__main__":
    from nature_style import (apply_style, clean_axes, panel, panel_letter,
                              DIVERGING, MONTHS, SEQ_BLUE)

    rng = np.random.default_rng(11)
    p = panel(placed_mm=180, aspect=0.62, draw_scale=2.0)
    apply_style(p)
    fig = plt.figure(figsize=p.figsize)
    axes, _ = ragged_grid(fig, 8, 4)

    # a -- distributions, unbalanced on purpose: group x is n = 9 and the
    #      violin is as wide as the others until the counts are shown.
    groups = [rng.gamma(3 + i * 0.4, 1.2, size=n)
              for i, n in enumerate([300, 220, 9, 180])]
    sm = violin_box(axes[0], groups, colors=MONTHS[::3], spec=p, show_n=True,
                    labels=list("vwxy"))
    axes[0].set_ylabel(r"Yield (t ha$^{-1}$)")

    # b -- coefficients, ordered once and kept
    names = ["Irradiance", "Wind speed", "Demand", "Storage", "Slope"]
    est = np.array([0.42, -0.21, 0.06, 0.55, -0.38])
    half = np.array([0.11, 0.09, 0.19, 0.14, 0.12])
    forest(axes[1], names, est, est - half, est + half, spec=p)
    axes[1].set_xlabel(r"Standardised $\beta$")

    # c -- composition, with the total as its own mark
    xs = np.arange(5)
    comp = {"Renewable": np.array([3.0, 4, 5, 6, 7]),
            "Storage": np.array([1.0, 1.5, 2, 2.2, 2.4]),
            "Conventional": np.array([4.0, 3, 2, 1.5, 1])}
    stacked_bars(axes[2], xs, comp, colors=["#4C72B0", "#DDAA33", "#808080"],
                 spec=p, value_labels=lambda v: f"{v:.0f}")
    axes[2].set_xticklabels([f"S{i}" for i in xs])
    axes[2].set_ylabel(r"Cost (USD capita$^{-1}$)")

    # d -- signed composition: the net is the claim
    signed = {"Inflow": np.array([3.0, 4, 5, 2, 1]),
              "Outflow": np.array([-2.0, -5, -1, -3, -4])}
    stacked_bars(axes[3], xs, signed, colors=["#0B75B3", "#C84747"],
                 spec=p, signed=True)
    axes[3].set_ylabel("Net flow (GWh)")

    # e -- grouped bars with intervals, never stars
    vals = np.array([[3.0, 4, 5], [4.0, 5, 6], [5.0, 5.5, 7]])
    ci = np.dstack([vals - 0.6, vals + 0.6])
    grouped_bars(axes[4], np.arange(3), vals, ci=ci, spec=p,
                 colors=["#E64B35", "#4DBBD5", "#00A087"])
    axes[4].set_ylabel("Rate (%)")

    # f -- fit with a band that stops at the data
    fx = rng.normal(10, 3, 4000)
    fy = 2.5 * fx + rng.normal(0, 6, 4000) + 4
    st = fit_line(axes[5], fx, fy, spec=p)
    axes[5].set_xlabel("Predictor (unit)")

    # g -- the same pairs as a density, because 4000 points is not a scatter
    mesh, _, _ = density_field(axes[6], fx, fy, spec=p, cmap="Blues", log=True)
    axes[6].set_xlabel("Predictor (unit)")
    cb = fig.colorbar(mesh, ax=axes[6], pad=0.02, fraction=0.05)
    cb.set_label("Count")            # a density panel without one is unreadable
    cb.outline.set_linewidth(0.4 * p.draw_scale)

    # h -- a correlation matrix, centred and half-masked
    X = rng.normal(size=(200, 6))
    X[:, 1] += X[:, 0] * 1.5
    X[:, 2] -= X[:, 0]
    mesh_m = matrix_panel(axes[7], np.corrcoef(X.T), labels=list("abcdef"),
                          spec=p, triangle="lower")
    cbm = fig.colorbar(mesh_m, ax=axes[7], pad=0.02, fraction=0.05)
    cbm.set_label("Pearson r")
    cbm.outline.set_linewidth(0.4 * p.draw_scale)

    for i, ax in enumerate(axes):
        if i not in (6, 7):
            clean_axes(ax)
        panel_letter(ax, chr(97 + i))

    fig.tight_layout()
    fig.savefig("demo_panels.png", dpi=200, bbox_inches="tight")

    # A state timeline is a wide panel; it gets its own figure.
    p2 = panel(placed_mm=180, aspect=0.22, draw_scale=2.0)
    apply_style(p2)
    fig2, ax = plt.subplots(figsize=p2.figsize)
    t = np.arange(0, 24, 1 / 12)
    power = np.clip(np.sin((t - 6) / 12 * np.pi), 0, None) * 3200
    power *= 1 - 0.5 * (rng.random(t.size) < 0.08)
    watts, unit, _ = auto_unit(power, "W")
    parked = (t % 24 < 7) | (t % 24 > 19)
    # Shading arrives in blocks, not as independent samples: a state column
    # that flickers every sample is a sampling artefact, and min_length is
    # what keeps those out of the panel.
    shaded = np.zeros(t.size, dtype=bool)
    for start in (8.6, 12.4, 14.2, 15.0):
        shaded |= (t >= start) & (t < start + 0.45)
    shaded |= rng.random(t.size) < 0.02          # single-sample flicker
    state_bands(ax, runs(parked, t), "#FDDBC7", label="Parked", alpha=0.5)
    state_bands(ax, runs(shaded, t, min_length=3), "#aba197", label="Shaded",
                alpha=0.35, zorder=2)
    ax.plot(t, watts, color="#E64B35", lw=1.2 * p2.draw_scale, zorder=4)
    clean_axes(ax)
    headroom(ax, watts)
    ax.set_xlim(0, 24)
    ax.set_xticks(np.arange(0, 25, 3))
    ax.set_xlabel("Hour of day")
    ax.set_ylabel(f"Power ({unit})")
    ax.legend(frameon=False, ncol=2, loc="upper left")
    fig2.tight_layout()
    fig2.savefig("demo_panels_timeline.png", dpi=200, bbox_inches="tight")

    print(f"violin group sizes : {[d['n'] for d in sm]}")
    print(f"fit                : slope={st['slope']:.3f} r2={st['r2']:.3f} "
          f"n={st['n']}")
    print(f"auto unit          : W -> {unit}")
    print("wrote demo_panels.png, demo_panels_timeline.png")
