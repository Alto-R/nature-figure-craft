# SPDX-FileCopyrightText: 2026 Churui Huang
# SPDX-License-Identifier: MIT

"""Paths and PDF inspection shared by the tests."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ASSETS = ROOT / "nature-figure-production" / "assets"
CHOOSER_ASSETS = ROOT / "chart-type-chooser" / "assets"

_FONT_PROGRAMS = ("/FontFile", "/FontFile2", "/FontFile3")


def _resolve(obj):
    return None if obj is None else obj.get_object()


def pdf_fonts(path) -> dict[str, tuple[str, bool]]:
    """Map each font a PDF uses to (subtype, has an embedded font program).

    Walks form XObjects as well as page resources: cairo draws translucent
    content inside transparency groups, and their fonts live there. A Type 3
    font counts as embedded (its glyphs are drawn inline) -- whether Type 3 is
    acceptable is a separate question the caller asks via the subtype.
    """
    from pypdf import PdfReader

    found: dict[str, tuple[str, bool]] = {}

    def walk(resources):
        resources = _resolve(resources)
        if resources is None:
            return
        for ref in (_resolve(resources.get("/Font")) or {}).values():
            font = _resolve(ref)
            subtype = str(font.get("/Subtype"))
            holder = font
            if subtype == "/Type0":
                holder = _resolve(_resolve(font["/DescendantFonts"])[0])
            desc = _resolve(holder.get("/FontDescriptor"))
            embedded = subtype == "/Type3" or (
                desc is not None and any(k in desc for k in _FONT_PROGRAMS))
            name = str(font.get("/BaseFont", font.get("/Name", "?")))
            found[name] = (subtype, embedded)
        for ref in (_resolve(resources.get("/XObject")) or {}).values():
            xobj = _resolve(ref)
            if xobj.get("/Subtype") == "/Form":
                walk(xobj.get("/Resources"))

    for page in PdfReader(str(path)).pages:
        walk(page.get("/Resources"))
    return found
