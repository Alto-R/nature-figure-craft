"""
nature_style.py -- drop-in style module for Nature-branded journal figures.

Usage
-----
    from nature_style import (apply_style, panel, landed_report, save_all,
                              export_legend, SINGLE_COL, DOUBLE_COL,
                              ACADEMIC, SEMANTIC_EXAMPLE, lighten, darken,
                              panel_letter, clean_axes,
                              DIVERGING, diverging_cmap, palette_report)

    p = panel(placed_mm=60, aspect=0.8)   # where it sits in the final figure
    apply_style(p)
    fig, ax = plt.subplots(figsize=p.figsize)
    ...
    clean_axes(ax)
    panel_letter(ax, 'a')
    landed_report(fig, p)                 # measure before you export
    save_all('fig1_a_timeseries', fig)

Design rules encoded here
-------------------------
* Type size is expressed as LANDED points -- what the reader measures on the
  printed page -- and derived from where the panel will be PLACED, not from how
  big the script happens to draw it. panel() does the arithmetic;
  landed_report() verifies it against the real Text artists. House target is
  9-10.5 pt body; the artwork guide's 5-7 pt window is kept in JOURNAL_WINDOW
  and reported, not enforced. See the comment above LANDED_MIN for why.
* Everything geometric (rules, ticks, markers) scales with type, so a panel
  shrunk at assembly keeps its intended weight.
* pdf.fonttype = 42 keeps text editable, as the journal artwork guide requires.
* Mathtext font is forced to Arial so `$^{-1}$` matches the surrounding label.
* save_all writes PDF (journal + assembly), SVG (vector editing), PNG (preview).
* The palette gallery is a set of worked starting points, not a requirement.
  Pick one diverging ramp, one sequential ramp and one qualitative set per
  paper. palette_report() checks a palette in CIE L* before it propagates
  through twenty figures; references/palettes.md has the reasoning.

Nothing here depends on a specific project or discipline.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

__all__ = [
    "MM", "SINGLE_COL", "DOUBLE_COL", "SINGLE_COL_OTHER", "DOUBLE_COL_OTHER",
    "TRIPLE_COL_OTHER", "MAX_H",
    "FS_BODY", "FS_TICK", "FS_PANEL", "body_pt_for",
    "LANDED_MIN", "LANDED_MAX", "LANDED_TOLERATED", "JOURNAL_WINDOW",
    "ACADEMIC", "SEMANTIC_EXAMPLE", "COLOR_SIM", "COLOR_REAL", "COLOR_BASELINE",
    "GREY", "CMAP",
    "DIVERGING", "MONTHS", "DIVERGING_WARM", "DIVERGING_GAP",
    "SEQ_BLUE", "SEQ_GREEN", "SEQ_RED", "SEQ_TEAL",
    "CLASSES6", "SCENARIO",
    "NPG", "AAAS", "NEJM", "JAMA", "QUALITATIVE_LARGE",
    "CONTRAST", "BAND", "TWO_FACTOR", "REGION_FILL", "REGION_MARK", "ZONE",
    "diverging_cmap", "lightness", "palette_report",
    "apply_style", "panel", "landed_report", "clean_axes", "panel_letter",
    "share_outer_labels", "reference_line", "percent_axis", "sci_axis",
    "lighten", "darken", "shade_ramp",
    "save_all", "export_legend", "set_outdir",
]

# --------------------------------------------------------------------------
# Physical sizes (Nature branded research journals, original research content)
# --------------------------------------------------------------------------

MM = 1 / 25.4

SINGLE_COL = 88 * MM        # 3.4646 in
DOUBLE_COL = 180 * MM       # 7.0866 in

# Non-research content types
SINGLE_COL_OTHER = 58 * MM
DOUBLE_COL_OTHER = 121 * MM
TRIPLE_COL_OTHER = 185 * MM

# Maximum figure height, keyed by caption length. MAX_H[caption_words][columns]
MAX_H = {
    300: {"single": 130 * MM, "double": 185 * MM},
    150: {"single": 180 * MM, "double": 210 * MM},
    50:  {"single": 220 * MM, "double": 225 * MM},
}

# --------------------------------------------------------------------------
# Type sizes
#
# There are TWO different numbers and confusing them is the most common
# figure-production error:
#
#   LANDED pt  -- what the reader measures on the printed page. This is what
#                 the journal constrains.
#   DRAWN pt   -- what you type into the script. Equals landed pt only if the
#                 panel is placed at exactly the width it was drawn at.
#
#       landed_pt = drawn_pt * (placed_width_mm / drawn_width_mm)
#
# A real main figure is 10-25 panels assembled in a vector tool, and almost
# every panel is SHRUNK on the way in -- you draw a scatter at a comfortable
# 110 mm and it ends up occupying 55 mm of a 180 mm figure. A script that
# hard-codes 7 pt therefore lands at 3.5 pt and is rejected. So the number to
# fix is the LANDED size, and the drawn size is derived from the placement.
#
# The landed target is a RANGE, not a constant, and it depends on how wide the
# panel actually is. Type does not scale linearly with panel size: 6 pt reads
# comfortably across a 180 mm panel but looks microscopic inside a 45 mm inset,
# where the reader's eye is comparing it against a much smaller frame. Small
# panels want proportionally LARGER type. See body_pt_for().
# --------------------------------------------------------------------------

# The official Nature artwork guide asks for 5-7 pt as landed on the page. That
# window is kept here as a documented fact, and landed_report still says when a
# figure sits outside it -- but it is NOT the house target.
#
# Reason: 5-7 pt is a floor-level legibility spec written for print, and figures
# built to the letter of it read as cramped on screen, in talks, and in the PDFs
# people actually skim. Accepted figures routinely run larger, landing around
# 9-12 pt. Art editors
# reset house style at production anyway, so the practical cost of being over the
# guide is close to zero, and the practical cost of being at the floor is a figure
# nobody can read without zooming.
JOURNAL_WINDOW = (5.0, 7.0)   # what the artwork guide asks for; reported, not enforced

LANDED_MIN = 5.0         # hard floor -- below this is a real reject
LANDED_MAX = 10.5        # house target ceiling (largest default body below)
LANDED_TOLERATED = 12.0  # absolute ceiling; above this is a real failure

# Default LANDED body size by placed panel width. Biased upward for narrow
# panels. Widths in mm, sizes in points.
BODY_PT_BY_WIDTH = [
    (160, 9.0),    # full double-column panel
    (100, 9.5),    # half to two-thirds of a double-column figure
    (60,  10.0),   # single column, or one of three across
    (0,   10.5),   # inset / small multiple
]


def body_pt_for(placed_mm: float) -> float:
    """Default LANDED body size for a panel of this placed width."""
    for w, pt in BODY_PT_BY_WIDTH:
        if placed_mm >= w:
            return pt
    return BODY_PT_BY_WIDTH[-1][1]


FS_BODY = 9.5    # landed: axis labels, annotations (default; see body_pt_for)
FS_TICK = 9.0    # landed: tick labels, legend text
FS_PANEL = 11.0  # landed: panel letters (bold)

# --------------------------------------------------------------------------
# Colour
# --------------------------------------------------------------------------

# General-purpose qualitative palette. Cycle in order; stop at six.
ACADEMIC = ["#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F", "#8491B4"]

# Two-series contrast
COLOR_SIM = "#d2352c"        # simulated / predicted
COLOR_REAL = "#4a7db3"       # measured / observed
COLOR_BASELINE = "#333333"   # baseline, drawn dashed

# Neutral tones, for whatever a figure wants to keep visually quiet. Optional --
# nothing in this module requires you to use them.
GREY = {
    "land": "#E8E8E8",
    "fill": "#F2F2F2",
    "line": "#888888",
    "faint": "#AAAAAA",
    "text": "#404040",
    "dark": "#333333",
}

# A semantic dictionary maps one PHYSICAL QUANTITY to one colour, fixed for the
# whole paper. Readers learn the code from the first figure and stop reading
# legends.
#
# The six hexes below are a worked example of the PATTERN -- one dict, defined
# once, imported everywhere -- not a recommended palette. Replace both the keys
# and the colours.
SEMANTIC_EXAMPLE = {
    "Component A": "#4C72B0",
    "Component B": "#DDAA33",
    "Component C": "#808080",
    "Component D": "#8172B3",
    "Component E": "#d47d49",
    "Component F": "#C44E52",
}

# Colormap selection guide, as data
CMAP = {
    "diverging_zero":   "RdBu_r",     # use with TwoSlopeNorm(vcenter=0)
    "diverging_alt":    "seismic",
    "probability":      "RdYlBu_r",
    "density":          "Blues",      # use with LogNorm for long tails
    "intensity":        "inferno",
    "cost_benefit":     "RdYlGn",
    "spatiotemporal":   "Spectral_r",
    "sequential":       "viridis",
    "sequential_cvd":   "cividis",    # colour-blind optimised
}

# --------------------------------------------------------------------------
# Palette gallery -- worked schemes, with the reasoning in references/palettes.md
#
# These are reusable STARTING POINTS, not a house requirement. Pick one
# diverging ramp, one sequential ramp and one qualitative set for the whole
# paper and use those three everywhere, supplement included.
# --------------------------------------------------------------------------

# Diverging: signed quantities, anomalies, residuals, differences from a
# baseline. Blue-red is the colour-blind-safe diverging axis.
#
# The visually neutral stop is index 7 of 13, so it lands at 7/12 = 0.583 with
# evenly spaced stops -- use diverging_cmap() below, or TwoSlopeNorm, to put
# zero at the pale colour. The navy end is also ~17 L* darker than the brick
# end, so negatives read heavier; use DIVERGING_WARM when the two directions
# must carry equal weight.
DIVERGING = [
    "#012A61", "#015696", "#0B75B3", "#4596CD", "#89CAEA", "#BBE6FA",
    "#E2F4FE", "#F1EEED", "#FCCDC9", "#EE9D9F", "#DE6A69", "#C84747",
    "#982B2D",
]

# Twelve steps of the same family, for months: cold months blue, warm months
# red, so the colour restates a variable the reader already holds. Not cyclic --
# December and January sit at opposite ends.
MONTHS = DIVERGING[:12]

# Diverging with a cream midpoint and balanced ends (L* 18.0 vs 24.2). Better
# than DIVERGING for filled areas, where a near-white middle reads as missing
# data against the page.
DIVERGING_WARM = ["#012f48", "#669aba", "#fbf0d9", "#be1420", "#7a0101"]

# Asymmetric diverging: six stops on the failing side, two on the succeeding
# side, for when one tail is the finding and the other is only context. Say so
# in the caption -- an unannounced non-linear colour scale is an integrity issue.
DIVERGING_GAP = ["#d73221", "#e35235", "#e48070", "#fcb777", "#fde699",
                 "#fef4ae", "#d2edf2", "#6491c1"]

# Sequential, single hue: lightness is monotone, so these survive greyscale and
# every form of colour-vision deficiency unmodified. Give each physical quantity
# its own hue and vary lightness within it, rather than mixing them into one ramp.
SEQ_BLUE = ["#c6dbef", "#6baed6", "#2171b5", "#084594"]
SEQ_GREEN = ["#c7e9c0", "#74c476", "#238b45", "#005a32"]
SEQ_RED = ["#fff5f0", "#fcbba1", "#fc9272", "#ef3b2c", "#99000d"]

# Muted sequential for the SECOND colour-coded layer of a panel whose main layer
# already uses a diverging ramp. Far enough from both blue-red ends to not be
# confused with them, quiet enough not to compete.
SEQ_TEAL = ["#ffffff", "#cfe3e3", "#9fc8c8", "#5fa3a3", "#2f7a7a"]

# Ordered classes: the ramp does the legend's job -- the reader can rank the
# classes without reading their names. Six-class slice of the DIVERGING family,
# for a two-threshold partition (see nature_quadrant.partition_legend).
# Caveat: the two middle classes are only 8.4 L* apart. Dual-encode them if the
# argument turns on telling them apart.
CLASSES6 = ["#012A61", "#0B75B3", "#89CAEA", "#F0D2D2", "#DC5654", "#982B2D"]

# Ordinal scenarios/horizons in one hue: darker = later/stronger/more. Costs one
# hue, not three. shade_ramp() generalises this to any base colour.
SCENARIO = {"2030": "#9ecae1", "2040": "#4292c6", "2050": "#08519c"}

# Qualitative sets reverse-engineered from major journal house styles. Pick ONE
# per paper and cycle it in order -- entries 0 and 1 are the strongest contrast
# pair, so a two-series panel gets the best separation for free. ACADEMIC above
# is NPG[:6] and stays the default cycler.
NPG = ["#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F",
       "#8491B4", "#91D1C2", "#DC0000", "#7E6148", "#B09C85"]
AAAS = ["#3B4992", "#EE0000", "#008B45", "#631879", "#008280",
        "#BB0021", "#5F559B", "#A20056", "#808180", "#1B1919"]
NEJM = ["#BC3C29", "#0072B5", "#E18727", "#20854E", "#7876B1",
        "#6F99AD", "#FFDC91", "#EE4C97"]
JAMA = ["#374E55", "#DF8F44", "#00A1D5", "#B24745", "#79AF97",
        "#6A6599", "#80796B"]

# Concatenated, ~35 distinguishable colours. Legitimate ONLY where colour is an
# identity lookup ("where is Japan") and never a comparison ("is orange bigger").
QUALITATIVE_LARGE = NPG + AAAS + NEJM + JAMA

# Two-colour contrasts, all drawn from the ends of DIVERGING so a paper has one
# colour system rather than five.
CONTRAST = {
    "positive": "#0B75B3", "negative": "#982B2D",
    "above": "#0B75B3", "below": "#DE6A69",
    "feasible": "#4C72B0", "infeasible": "#C44E52",
    "significant": "#982B2D", "not_significant": "#0B75B3",
}

# Green-amber-red threshold bands. Instantly readable and NOT colour-blind safe:
# use only where the class is also carried by text or position.
BAND = ["#009988", "#DD8452", "#C44E52"]

# Two crossed binary factors: hue carries one, lightness the other, so a reader
# decomposes the legend instead of memorising it. Pairs are ~36 L* apart, so the
# lightness factor alone survives greyscale.
TWO_FACTOR = ["#FDAE61", "#BD0026", "#ABD9E9", "#2C7BB6"]

# Region plots: a fill and a mark per region. Fills sit within 8 L* of each
# other, so no region looks more important than another; each mark is the same
# hue at higher saturation, clearing its own fill by 15-35 L*.
REGION_FILL = {"Q1": "#d5e8f1", "Q2": "#a9d9bb", "Q3": "#f6dfd6", "Q4": "#cfcce3"}
REGION_MARK = {"Q1": "#4a9cc7", "Q2": "#5ab87a", "Q3": "#c07060", "Q4": "#8a85b0"}

# Background bands for logical partitions; draw at alpha 0.10-0.20, zorder 0.
ZONE = {"low": "#ABD3A0", "mid": "#FBEA2E", "high": "#EC3E31"}


def diverging_cmap(colors=None, neutral=None, name="diverging", n=256):
    """Diverging colormap with its neutral stop pinned to 0.5.

    A list of hexes handed to LinearSegmentedColormap.from_list is spaced
    evenly, which puts the pale middle at index/(len-1) -- not at 0.5 unless the
    list happens to be odd and symmetric. That silently decouples the visual
    centre from zero. This pins it.

    colors  ramp, neutral in the middle (default: DIVERGING)
    neutral index of the neutral stop (default: the least saturated colour)

    The default picks the LEAST SATURATED stop, not the lightest. On a ramp
    whose two arms are unequally long the palest colour is often still visibly
    tinted -- DIVERGING's lightest stop is a pale blue, one place before the
    achromatic one -- and "no signal" is where the hue vanishes, not where the
    lightness peaks.
    """
    colors = list(colors if colors is not None else DIVERGING)
    if neutral is None:
        def chroma(c):
            r, g, b = mcolors.to_rgb(c)[:3]
            return max(r, g, b) - min(r, g, b)
        neutral = min(range(len(colors)), key=lambda i: chroma(colors[i]))
    last = len(colors) - 1
    if not 0 < neutral < last:
        raise ValueError("neutral must be an interior stop")
    pos = ([i / neutral * 0.5 for i in range(neutral + 1)]
           + [0.5 + (i - neutral) / (last - neutral) * 0.5
              for i in range(neutral + 1, len(colors))])
    return mcolors.LinearSegmentedColormap.from_list(
        name, list(zip(pos, colors)), N=n)


def lightness(color):
    """Approximate CIE L* (0 black, 100 white) of any matplotlib colour.

    Lightness -- not hue -- decides whether a palette survives greyscale
    printing and colour-vision deficiency. Categories that must be told apart
    want more than ~10 points between them.
    """
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in mcolors.to_rgb(color)[:3])
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return 116 * (y ** (1 / 3) if y > 0.008856 else 7.787 * y + 16 / 116) - 16


def palette_report(colors, labels=None, min_gap=10.0, ordered=False, name=""):
    """Print the L* of a palette and find pairs that collide in greyscale.

    Run this before a palette propagates through twenty figures. Returns the
    list of (entry, entry, gap) pairs closer than min_gap.

    ordered=True for a ramp read as DISCRETE ranked classes -- an ordinal class
    ramp, a binned choropleth, a scenario ladder. Only CONSECUTIVE steps are
    checked,
    because that is the pair a reader has to separate. A diverging ramp is
    deliberately non-monotone in lightness -- its two arms mirror each other, so
    a mid-blue and a mid-red necessarily share a grey value and direction is
    carried by hue. Flagging those would be flagging the design. Consecutive
    steps that collide are a real defect: the ramp claims an order the reader
    cannot see. Fix by re-spacing the stops.

    Do NOT run this check on a stop list destined for LinearSegmentedColormap.
    There the stops are interpolation control points, not classes a reader ever
    separates, and closely spaced neighbours near the neutral are exactly what
    makes the ramp smooth -- DIVERGING has three such pairs by design.

    ordered=False (default) for a qualitative set, where the entries encode
    unrelated categories and every pair is checked. Close lightness is EXPECTED
    there, because six distinguishable hues cannot also be six distinguishable
    greys; the fix is to dual-encode (linestyle, marker, hatch), not to re-pick
    the colours.
    """
    items = list(colors.items()) if isinstance(colors, dict) else list(
        zip(labels or [str(i) for i in range(len(colors))], colors))
    header = f"palette_report: {name}" if name else "palette_report"
    print(f"{header}  ({'ordered ramp' if ordered else 'qualitative set'})")
    print(f"  {'entry':<24} {'hex':<10} L*")
    for label, c in items:
        print(f"  {label:<24} {str(c):<10} {lightness(c):5.1f}")

    pairs = (list(zip(items, items[1:])) if ordered else
             [(items[i], items[j]) for i in range(len(items))
              for j in range(i + 1, len(items))])
    close = [(a, b, abs(lightness(ca) - lightness(cb)))
             for (a, ca), (b, cb) in pairs
             if abs(lightness(ca) - lightness(cb)) < min_gap]

    scope = "consecutive step" if ordered else "pair"
    if not close:
        print(f"  OK    every {scope} separated by >= {min_gap} L*; "
              f"survives greyscale unaided")
    elif ordered:
        worst = min(close, key=lambda t: t[2])
        print(f"  FAIL  {len(close)} consecutive step(s) under {min_gap} L*, "
              f"closest {worst[0]} / {worst[1]} at {worst[2]:.1f}. An ordered "
              f"ramp whose neighbouring steps collide is claiming a rank the "
              f"reader cannot see -- re-space the stops.")
    else:
        print(f"  NOTE  {len(close)} pair(s) under {min_gap} L*. Normal for a "
              f"qualitative set: dual-encode with linestyle / marker / hatch "
              f"so colour is never the only channel.")
    return close

# --------------------------------------------------------------------------
# Global style
# --------------------------------------------------------------------------


def apply_style(spec=None, body: float = None, tick: float = None,
                scale: float = None, tick_direction: str = "out",
                serif: bool = False, label: float = None) -> None:
    """Install the journal rcParams. Call once at the top of every script.

    Parameters
    ----------
    spec : a Panel from panel(). Supplies body/tick sizes and the draw scale in
        one argument -- the normal way to call this. `apply_style(p)`.
    body, tick : LANDED point sizes, if you are not using a Panel. `body` is
        the in-plot annotation size; `tick` covers tick labels, axis labels and
        legend text, which are deliberately all the same.
    label : LANDED axis-label size. Defaults to `tick`, i.e. axis labels match
        their own tick labels and the legend. Raise it only if a panel is
        placed so small that its labels vanish.
    scale : draw-scale multiplier, if you are not using a Panel. Multiplies
        every type size, line width, tick length and marker size together, so
        the panel looks identical once shrunk back to its placed width.
    tick_direction : 'out' or 'in'. Free choice, but must be identical across
        every figure in the paper.
    serif : set True only if the manuscript body text is serif and the target
        journal expects matching figure type.
    """
    letter = FS_PANEL
    if spec is not None:
        body = spec.body if body is None else body
        tick = spec.tick if tick is None else tick
        scale = spec.draw_scale if scale is None else scale
        letter = spec.letter
    body = FS_BODY if body is None else body
    tick = FS_TICK if tick is None else tick
    scale = 1.0 if scale is None else scale
    # Axis labels, tick labels and legend text are ONE size. An axis label set
    # larger than its own ticks reads as a heading for the panel, which is the
    # job the caption already does; and a legend at a size of its own makes a
    # multi-panel figure look assembled from parts. `body` stays available for
    # in-plot annotations, which do want to be a step up.
    label = tick if label is None else label

    family = "serif" if serif else "sans-serif"
    face = "Times New Roman" if serif else "Arial"
    body = body * scale
    tick = tick * scale
    label = label * scale

    mpl.rcParams.update({
        # --- typography -------------------------------------------------
        "font.family": family,
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": body,
        "axes.labelsize": label,
        "axes.titlesize": label,
        "xtick.labelsize": tick,
        "ytick.labelsize": tick,
        "legend.fontsize": tick,
        # panel_letter() reads this; it is the letter size, not a real title
        "figure.titlesize": letter * scale,

        # mathtext must match the body face, or $^{-1}$ renders in DejaVu
        "mathtext.fontset": "custom",
        "mathtext.rm": face,
        "mathtext.it": f"{face}:italic",
        "mathtext.bf": f"{face}:bold",
        "mathtext.default": "regular",
        "axes.unicode_minus": False,

        # --- geometry (scales with type, or line weights break on shrink) --
        "axes.linewidth": 0.6 * scale,
        "lines.linewidth": 1.0 * scale,
        "lines.markersize": 3.0 * scale,
        "patch.linewidth": 0.4 * scale,
        "xtick.major.width": 0.6 * scale,
        "ytick.major.width": 0.6 * scale,
        "xtick.minor.width": 0.4 * scale,
        "ytick.minor.width": 0.4 * scale,
        "xtick.major.size": 2.5 * scale,
        "ytick.major.size": 2.5 * scale,
        "xtick.minor.size": 1.5 * scale,
        "ytick.minor.size": 1.5 * scale,
        "xtick.direction": tick_direction,
        "ytick.direction": tick_direction,

        # --- grid & legend ----------------------------------------------
        "axes.grid": False,
        "grid.linestyle": "--",
        "grid.linewidth": 0.4 * scale,
        "grid.alpha": 0.3,
        "legend.frameon": False,
        "legend.handlelength": 1.6,
        "legend.handletextpad": 0.6,
        "legend.columnspacing": 2.0,

        # --- colour cycle -----------------------------------------------
        "axes.prop_cycle": mpl.cycler(color=ACADEMIC),

        # --- export -----------------------------------------------------
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "savefig.transparent": False,
        "pdf.fonttype": 42,       # TrueType -> text stays editable (REQUIRED)
        "ps.fonttype": 42,
        "svg.fonttype": "none",   # keep SVG text as text
    })


class Panel:
    """The geometry contract for one panel of an assembled figure.

    Attributes
    ----------
    placed_mm  : width this panel will occupy in the final assembled figure.
                 This is the number the reader's ruler sees.
    drawn_mm   : width the script actually renders at (placed_mm * draw_scale).
    draw_scale : working-comfort knob only. Because type, rules, ticks and
                 markers are ALL multiplied by it, the landed result is
                 identical at any draw_scale. Raise it if you want to eyeball
                 the PNG without zooming; it changes nothing on the page.
    body/tick/letter : LANDED point sizes.
    figsize    : hand straight to plt.subplots(figsize=...).
    """

    __slots__ = ("placed_mm", "placed_h_mm", "drawn_mm", "drawn_h_mm",
                 "draw_scale", "body", "tick", "letter", "figsize")

    def __init__(self, placed_mm, placed_h_mm, draw_scale, body, tick, letter):
        self.placed_mm = placed_mm
        self.placed_h_mm = placed_h_mm
        self.draw_scale = draw_scale
        self.body, self.tick, self.letter = body, tick, letter
        self.drawn_mm = placed_mm * draw_scale
        self.drawn_h_mm = placed_h_mm * draw_scale
        self.figsize = (self.drawn_mm * MM, self.drawn_h_mm * MM)

    def __repr__(self):
        return (f"Panel(placed={self.placed_mm:.0f}x{self.placed_h_mm:.0f} mm, "
                f"drawn={self.drawn_mm:.0f}x{self.drawn_h_mm:.0f} mm, "
                f"draw_scale={self.draw_scale:g}, "
                f"landed body/tick/letter = "
                f"{self.body:g}/{self.tick:g}/{self.letter:g} pt)")


def panel(placed_mm: float, height_mm: float = None, aspect: float = 0.75,
          draw_scale: float = 1.0, body_pt: float = None) -> Panel:
    """Declare where a panel will sit in the assembled figure, get its figsize.

    This replaces "set figsize to the final size and hard-code 7 pt". That rule
    is only correct when the figure is a single panel placed at full width. A
    real main figure is many panels placed at many different widths, and the
    type size has to be derived from the placement, per panel.

    Usage
    -----
        # this panel will occupy 60 mm of a 180 mm three-across figure
        p = panel(placed_mm=60, aspect=0.8)
        apply_style(p)
        fig, ax = plt.subplots(figsize=p.figsize)
        ...
        landed_report(fig, p)

    Parameters
    ----------
    placed_mm : width the panel occupies in the assembled figure.
    height_mm : placed height. Defaults to placed_mm * aspect.
    aspect : height / width, used only when height_mm is None.
    draw_scale : render this many times larger than placed, for comfort only.
        Does not affect the landed result -- see Panel.draw_scale.
    body_pt : override the LANDED body size. Default body_pt_for(placed_mm),
        which biases narrow panels upward.
    """
    if height_mm is None:
        height_mm = placed_mm * aspect
    body = body_pt if body_pt is not None else body_pt_for(placed_mm)
    tick = round(body - 0.5, 2)
    letter = min(body + 1.5, LANDED_TOLERATED)
    return Panel(placed_mm, height_mm, draw_scale, body, tick, letter)


def landed_report(fig, panel_or_placed_mm, verbose: bool = True):
    """Measure every text object in `fig` and report its size on the page.

    Walks the actual Text artists rather than trusting rcParams, so it catches
    hard-coded fontsize= arguments, seaborn overrides, and colorbar labels --
    which is where out-of-spec type nearly always hides.

    Returns (rows, n_violations); rows are (landed_pt, drawn_pt, count, sample).
    """
    from matplotlib.text import Text

    if isinstance(panel_or_placed_mm, Panel):
        placed_mm = panel_or_placed_mm.placed_mm
    else:
        placed_mm = float(panel_or_placed_mm)

    drawn_mm = fig.get_size_inches()[0] / MM
    shrink = placed_mm / drawn_mm

    buckets = {}
    for t in fig.findobj(Text):
        s = t.get_text()
        if not s or not s.strip():
            continue
        drawn_pt = t.get_fontsize()
        key = round(drawn_pt, 2)
        entry = buckets.setdefault(key, [0, s])
        entry[0] += 1

    rows = []
    violations = 0
    for drawn_pt in sorted(buckets, reverse=True):
        count, sample = buckets[drawn_pt]
        lp = drawn_pt * shrink
        ceiling = LANDED_TOLERATED if _is_panel_letter(sample) else LANDED_MAX
        if lp < LANDED_MIN or lp > LANDED_TOLERATED:
            state = "FAIL"
            violations += 1
        elif lp > ceiling:
            state = "over"          # outside the guide, but commonly accepted
        else:
            state = "ok"
        rows.append((lp, drawn_pt, count, sample, state))

    if verbose:
        print(f"panel drawn {drawn_mm:.1f} mm -> placed {placed_mm:.1f} mm "
              f"(shrink {shrink:.3f})")
        for lp, dp, count, sample, state in rows:
            snippet = sample if len(sample) <= 22 else sample[:19] + "..."
            print(f"  [{state:>4}] {dp:5.1f} pt drawn -> {lp:5.2f} pt landed  "
                  f"x{count:<4d} e.g. {snippet!r}")
        n_over = sum(1 for r in rows if r[4] == "over")
        print(f"  house target {LANDED_MIN:g}-{LANDED_MAX:g} pt "
              f"(hard ceiling {LANDED_TOLERATED:g}): "
              f"{violations} fail, {n_over} over")
        jlo, jhi = JOURNAL_WINDOW
        outside = sum(r[2] for r in rows if not (jlo <= r[0] <= jhi))
        if outside:
            print(f"  note: {outside} text object(s) sit outside the artwork "
                  f"guide's {jlo:g}-{jhi:g} pt window. This is the house target "
                  f"working as intended, not an error -- see JOURNAL_WINDOW.")
    return rows, violations


def _is_panel_letter(s: str) -> bool:
    """Panel letters are allowed one step above the body window."""
    return len(s) == 1 and s.isalpha() and s.islower()


# --------------------------------------------------------------------------
# Axes helpers
# --------------------------------------------------------------------------


def clean_axes(ax, grid_axis: str = "y", box: bool = False):
    """Remove top/right spines and apply the house grid.

    box=True keeps all four spines (heatmaps, matrices, shaded scatter panels).
    grid_axis=None disables the grid entirely.
    """
    if not box:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    if grid_axis:
        ax.grid(axis=grid_axis, linestyle="--", linewidth=0.4, alpha=0.3, zorder=0)
        if grid_axis == "y":
            ax.xaxis.grid(False)
        elif grid_axis == "x":
            ax.yaxis.grid(False)
    ax.set_axisbelow(True)
    return ax


def panel_letter(ax, letter: str, x: float = -0.14, y: float = 1.06,
                 size: float = None):
    """Nature-style panel label: lowercase, bold, no parentheses, top-left.

    size defaults to the current draw-scaled letter size, so the letter shrinks
    with the panel instead of landing at 4 pt.
    """
    if size is None:
        size = mpl.rcParams["figure.titlesize"]
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=size,
            fontweight="bold", va="top", ha="left")
    return ax


def share_outer_labels(axes, n_rows: int, n_cols: int,
                       xlabel: str | None = None, ylabel: str | None = None):
    """Keep axis labels only on the outer ring of a subplot grid."""
    flat = axes.flat if hasattr(axes, "flat") else axes
    for i, ax in enumerate(flat):
        row, col = divmod(i, n_cols)
        if col > 0:
            ax.set_ylabel("")
            ax.set_yticklabels([])
        elif ylabel:
            ax.set_ylabel(ylabel)
        if row < n_rows - 1:
            ax.set_xlabel("")
            ax.set_xticklabels([])
        elif xlabel:
            ax.set_xlabel(xlabel)
    return axes


def reference_line(ax, kind: str = "zero", value: float = 0.0,
                   color: str = COLOR_BASELINE, lw: float = 0.8, **kw):
    """Draw the line that tells the reader which direction is good.

    kind: 'zero' | 'hline' | 'vline' | 'diagonal'
    """
    style = dict(color=color, linewidth=lw, linestyle="--", zorder=1)
    style.update(kw)
    if kind in ("zero", "hline"):
        ax.axhline(value, **style)
    elif kind == "vline":
        ax.axvline(value, **style)
    elif kind == "diagonal":
        lo = max(ax.get_xlim()[0], ax.get_ylim()[0])
        hi = min(ax.get_xlim()[1], ax.get_ylim()[1])
        ax.plot([lo, hi], [lo, hi], **style)
    else:
        raise ValueError(f"unknown reference line kind: {kind}")
    return ax


def percent_axis(ax, axis: str = "y", xmax: float = 1.0):
    """Format an axis as percentages (data given as 0-1 by default)."""
    fmt = ticker.PercentFormatter(xmax)
    getattr(ax, f"{axis}axis").set_major_formatter(fmt)
    return ax


def sci_axis(ax, axis: str = "y", limits=(-3, 3)):
    """Scientific notation as x10^n, never 1e-3.

    Prefer a unit change (kWh -> MWh) over this. Only use when no natural
    larger unit exists.
    """
    ax.ticklabel_format(style="sci", axis=axis, scilimits=limits,
                        useMathText=True)
    return ax


# --------------------------------------------------------------------------
# Colour helpers
# --------------------------------------------------------------------------


def lighten(hex_color: str, f: float):
    """f=0 returns the original colour, f=1 returns white."""
    return tuple(c + (1 - c) * f for c in mcolors.to_rgb(hex_color))


def darken(hex_color: str, f: float):
    """f=0 returns the original colour, f=1 returns black."""
    return tuple(c * (1 - f) for c in mcolors.to_rgb(hex_color))


def shade_ramp(hex_color: str, n: int = 3, span: float = 0.65):
    """n same-hue shades from the base colour outward, for sub-categories."""
    if n == 1:
        return [mcolors.to_rgb(hex_color)]
    return [lighten(hex_color, span * i / (n - 1)) for i in range(n)]


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------

_OUTDIR = Path(".")


def set_outdir(path) -> None:
    """Set the parent directory that will contain pdf/, svg/, png/."""
    global _OUTDIR
    _OUTDIR = Path(path)


def save_all(base: str, fig=None, dpi: int = 300, formats=("pdf", "svg", "png"),
             **kw):
    """Export one panel to PDF (journal + assembly), SVG (editing), PNG (preview).

    Always call on the *panel*, not on an assembled composite -- complex main
    figures are assembled in a vector tool, not in matplotlib.
    """
    f = fig if fig is not None else plt.gcf()
    written = []
    for ext in formats:
        d = _OUTDIR / ext
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{base}.{ext}"
        if ext == "png":
            f.savefig(path, dpi=dpi, bbox_inches="tight", **kw)
        else:
            f.savefig(path, bbox_inches="tight", **kw)
        written.append(str(path))
    return written


def export_legend(handles, base: str, ncol: int = 1, figsize=(4, 1.5),
                  fontsize: float = None, **kw):
    """Render a legend as its own file so it can be placed freely at assembly.

    handles: list of Line2D / Patch artists carrying `label=`.

    The legend file must be drawn at the SAME draw_scale as the panels it will
    sit next to, or it will not match once everything is placed. fontsize
    defaults to the current scaled legend size, which does exactly that.
    """
    if fontsize is None:
        fontsize = mpl.rcParams["legend.fontsize"]
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")
    ax.legend(handles=handles, loc="center", frameon=False, ncol=ncol,
              fontsize=fontsize, handlelength=1.6, columnspacing=2.0,
              handletextpad=0.6, **kw)
    paths = save_all(base, fig)
    plt.close(fig)
    return paths


# --------------------------------------------------------------------------
# Self-test: python nature_style.py -> demo panel + legend in ./pdf ./svg ./png
# --------------------------------------------------------------------------

if __name__ == "__main__":
    import numpy as np
    from matplotlib.patches import Patch

    # This panel will occupy 88 mm of the assembled figure; draw it 2x for
    # comfort. draw_scale changes nothing about the landed result.
    p = panel(placed_mm=88, height_mm=56, draw_scale=2.0)
    apply_style(p)
    print(p)

    rng = np.random.default_rng(0)
    x = np.linspace(0, 24, 200)

    fig, ax = plt.subplots(figsize=p.figsize)
    for i, (name, color) in enumerate(list(SEMANTIC_EXAMPLE.items())[:3]):
        ax.plot(x, np.sin(x / 3 + i) + i * 0.4 + rng.normal(0, 0.03, x.size),
                color=color, label=name)
    ax.set_xlabel("Time (h)")
    ax.set_ylabel(r"Response (unit h$^{-1}$)")
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 6))
    clean_axes(ax)
    reference_line(ax, "zero")
    panel_letter(ax, "a")

    landed_report(fig, p)

    # Palette checks: the neutral of DIVERGING must land at 0.5, and every
    # semantic colour must be tellable from every other in greyscale.
    dc = diverging_cmap()
    got, want = mcolors.to_hex(dc(0.5)), DIVERGING[7]
    assert abs(lightness(got) - lightness(want)) < 0.5, \
        f"diverging_cmap put {got} at 0.5, expected the neutral {want}"
    print(f"\ndiverging_cmap: 0.5 -> {got} (neutral {want}, "
          f"L* {lightness(got):.1f})")
    palette_report(SEMANTIC_EXAMPLE, name="SEMANTIC_EXAMPLE")
    print()
    palette_report(CLASSES6, ordered=True, name="CLASSES6",
                   labels=[f"class {i + 1}" for i in range(len(CLASSES6))])

    save_all("demo_panel", fig)
    export_legend([Patch(facecolor=c, label=k) for k, c in SEMANTIC_EXAMPLE.items()],
                  "demo_legend", ncol=3, figsize=(DOUBLE_COL, 0.5))

    print("wrote pdf/, svg/, png/ demo_panel.* and demo_legend.*")
