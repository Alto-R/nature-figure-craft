# SPDX-FileCopyrightText: 2026 Churui Huang
# SPDX-License-Identifier: MIT

"""profile_data.py detects the structure a chart choice depends on."""

from __future__ import annotations

import json
import sys

import pandas as pd
import pytest

from support import CHOOSER_ASSETS

sys.path.insert(0, str(CHOOSER_ASSETS))
import profile_data  # noqa: E402


@pytest.fixture
def table():
    # 40 sites x 3 scenarios, with coordinates, a year, and one cost far out
    # in the tail. Deterministic, so the expectations below are exact.
    rows = []
    for i in range(40):
        for j, scenario in enumerate(["base", "high", "low"]):
            rows.append({
                "site": f"site{i:02d}",
                "scenario": scenario,
                "lat": 30 + 0.05 * i + 0.01 * j,
                "lon": 110 + 0.05 * i - 0.01 * j,
                "year": 2020 + i % 5,
                "cost": 1 + ((3 * i + j) % 7) / 10,
            })
    rows[0]["cost"] = 200.0
    return pd.DataFrame(rows)


def test_profile_detects_geo_time_facets_and_tail(table):
    p = profile_data.profile(table, "fixture")
    assert (p["n_rows"], p["n_cols"]) == (120, 6)
    assert p["geo"] is True
    assert p["by_kind"]["latitude"] == ["lat"]
    assert p["by_kind"]["longitude"] == ["lon"]
    assert p["temporal"] == ["year"]
    assert p["skewed"] == ["cost"]
    facets = {f["name"]: f for f in p["facets"]}
    assert facets["scenario"]["groups"] == {"base": 40, "high": 40, "low": 40}
    assert facets["site"]["n_levels"] == 40


def test_open_choices_follow_from_the_profile(table):
    p = profile_data.profile(table, "fixture")
    keys = {d["key"] for d in profile_data.decision_points(p)}
    assert {"map", "split:scenario", "scale:cost", "time:year"} <= keys


def test_cli_prints_profile_and_writes_json(table, tmp_path, capsys):
    csv = tmp_path / "fixture.csv"
    out = tmp_path / "profile.json"
    table.to_csv(csv, index=False)
    assert profile_data.main([str(csv), "--json", str(out)]) == 0
    assert "latitude/longitude present" in capsys.readouterr().out
    profiles = json.loads(out.read_text(encoding="utf-8"))
    assert len(profiles) == 1 and profiles[0]["geo"] is True
