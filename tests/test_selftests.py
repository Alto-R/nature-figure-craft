# SPDX-FileCopyrightText: 2026 Churui Huang
# SPDX-License-Identifier: MIT

"""Every Python asset with a self-test still runs it and writes its demo files.

Each self-test runs in a fresh directory, exactly as a user would run it, so a
broken import, a renamed helper or a failing export surfaces here.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from support import PRODUCTION_ASSETS, pdf_fonts

SELF_TESTS = {
    "nature_style.py": ["pdf/demo_panel.pdf", "svg/demo_panel.svg",
                        "png/demo_panel.png", "pdf/demo_legend.pdf"],
    "nature_panels.py": ["demo_panels.png", "demo_panels_timeline.png"],
    "nature_quadrant.py": ["demo_quadrant.png", "demo_quadrant_2x2.png",
                           "demo_quadrant_legend.png"],
}


def _run(script, cwd):
    env = {**os.environ, "MPLBACKEND": "Agg"}
    return subprocess.run([sys.executable, str(PRODUCTION_ASSETS / script)],
                          cwd=cwd, env=env, capture_output=True, text=True,
                          timeout=600)


@pytest.mark.parametrize("script, outputs", SELF_TESTS.items(),
                         ids=list(SELF_TESTS))
def test_self_test_writes_its_outputs(script, outputs, tmp_path):
    result = _run(script, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    for out in outputs:
        assert (tmp_path / out).stat().st_size > 0, out


def test_style_pdf_keeps_text_as_embedded_truetype(tmp_path):
    # spec.md: pdf.fonttype = 42 is required -- Type 3 turns text into outlines
    # that no one can edit, and an unembedded font renders as a substitute.
    assert _run("nature_style.py", tmp_path).returncode == 0
    fonts = pdf_fonts(tmp_path / "pdf" / "demo_panel.pdf")
    assert fonts, "no fonts found in the exported PDF"
    for name, (subtype, embedded) in fonts.items():
        assert subtype != "/Type3", f"{name} exported as Type 3"
        assert embedded, f"{name} is not embedded"


def test_map_module_imports_without_cartopy():
    # nature_map.py has no self-test (it needs real coordinates), but its
    # cartopy and geopandas imports are deferred, so the module must import
    # on a plain matplotlib install.
    code = f"import sys; sys.path.insert(0, {str(PRODUCTION_ASSETS)!r}); import nature_map"
    result = subprocess.run([sys.executable, "-c", code],
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
