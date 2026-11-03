# SPDX-FileCopyrightText: 2026 Churui Huang
# SPDX-License-Identifier: MIT

"""nature_chord.R exports PDFs whose fonts are all embedded.

Regression test for issue #1: pdf() + extrafont wrote Arial unembedded with
broken widths, and viewers rendered every label as garbage while the PNG
preview looked fine. Skipped where R or circlize is not installed. The CI job
that installs both sets REQUIRE_R_TESTS=1, which turns a skip into a failure,
so the check can never pass by silently not running.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

from support import PRODUCTION_ASSETS, pdf_fonts

RSCRIPT = shutil.which("Rscript")


def _unavailable(reason):
    if os.environ.get("REQUIRE_R_TESTS") == "1":
        pytest.fail(reason)
    pytest.skip(reason)


def _r(expr):
    return subprocess.run([RSCRIPT, "-e", expr], capture_output=True,
                          text=True, timeout=120).stdout.strip()


@pytest.fixture(scope="module")
def chord_dir(tmp_path_factory):
    if RSCRIPT is None:
        _unavailable("R is not installed")
    if _r('cat(requireNamespace("circlize", quietly = TRUE))') != "TRUE":
        _unavailable("circlize is not installed")
    if _r('cat(capabilities("cairo"))') != "TRUE":
        _unavailable("R without cairo falls back to unembedded base-14 Helvetica")
    out = tmp_path_factory.mktemp("chord")
    result = subprocess.run([RSCRIPT, str(PRODUCTION_ASSETS / "nature_chord.R")],
                            cwd=out, capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stdout + result.stderr
    return out


@pytest.mark.parametrize("name", ["demo_chord_ungrouped.pdf",
                                  "demo_chord_grouped.pdf",
                                  "demo_chord_legend.pdf"])
def test_chord_pdf_embeds_every_font(chord_dir, name):
    fonts = pdf_fonts(chord_dir / name)
    assert fonts, "no fonts found -- the labels were not written as text"
    missing = [n for n, (_, embedded) in fonts.items() if not embedded]
    assert not missing, f"fonts not embedded: {missing}"


def test_chord_png_preview_written(chord_dir):
    for name in ["demo_chord_ungrouped.png", "demo_chord_grouped.png"]:
        assert (chord_dir / name).stat().st_size > 0, name
