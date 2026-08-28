# Production workflow

How a real multi-panel journal figure is built. This is the layer that separates a
figure that *plots correctly* from one that *submits cleanly*, and it is almost never
taught.

## Table of contents

1. The core insight
2. Repository layout
3. The shared style module
4. Panel-separated export
5. Standalone legend export
6. Triple-format export
7. Single source of truth for data
8. File-size management
9. Assembly in a vector tool
10. Icon libraries for schematics
11. Reproducibility
12. Pre-submission audit checklist

---

## 1. The core insight

**Do not build a complex main figure inside matplotlib.**

A published main figure typically contains 4–6 panels of heterogeneous types — a map,
a scatter with an inset, a stacked bar, a Sankey — at irregular sizes with a legend
tucked into whitespace. Forcing that into one `GridSpec` costs hours of
`subplots_adjust` fiddling, breaks whenever data changes, and still looks cramped.

The workflow used by actual published figures is:

```
render each panel independently  ->  export as vector PDF
export the legend as its own file
assemble on an 88 / 180 mm canvas in Illustrator (or PowerPoint)
```

Benefits:
- Panels can be repositioned, resized, and realigned in seconds.
- One panel can be re-rendered without touching the others.
- Text stays editable through the whole chain, satisfying the artwork requirement.
- The legend goes wherever there is space.

## 2. Repository layout

```
project/
├── source_data.xlsx          # single source of truth (also the journal's Source Data)
├── result/                   # model / analysis outputs
└── figures/
    ├── nature_style.py       # shared style module
    ├── fig1.py               # one script (or notebook) per main figure
    ├── fig2.py
    ├── suppfig7.py
    ├── pdf/                  # vector, for the journal and for assembly
    ├── svg/                  # vector, for Illustrator editing
    ├── png/                  # raster preview, for collaborators
    └── assembled/
        ├── fig1.ai
        └── fig1.pdf          # final artwork
```

## 3. The shared style module

One module, imported by every script. Changing a line weight once changes it
everywhere — that global consistency is what reads as "professional" more than any
single panel's polish.

```python
# figures/nature_style.py
from nature_style import apply_style, save_all, export_legend, COST, SINGLE_COL, DOUBLE_COL
apply_style()
```

See `../assets/nature_style.py` for a complete drop-in implementation.

## 4. Panel-separated export

Name panels so the mapping to the assembled figure is unambiguous:

```
pdf/fig2_a_world_map.pdf
pdf/fig2_b_quadrant_scatter.pdf
pdf/fig2_c_class_map.pdf
pdf/fig2_d_class_bars.pdf
pdf/fig2_legend_regions.pdf
pdf/fig2_legend_quadrants.pdf
```

An auto-numbering fallback (`fig2_01.pdf`, `fig2_02.pdf`, …) is convenient in
notebooks where every displayed figure should be captured:

```python
_N = [0]
def save_next(stem='fig2'):
    _N[0] += 1
    save_all(f'{stem}_{_N[0]:02d}')
```

Trade-off: auto-numbering is frictionless while iterating but produces opaque
filenames. Rename before assembly.

## 5. Standalone legend export

A legend rendered inside a panel is stuck there. Rendered as its own file, it can be
placed anywhere on the assembled canvas.

```python
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

handles = [Line2D([0], [0], color='black', lw=1.2, marker='o', ms=3,
                  label='Total cost trend')]
handles += [Patch(facecolor=c, label=k) for k, c in COST.items()]

export_legend(handles, 'fig2_legend', ncol=3, figsize=(7.09, 0.6))
```

Implementation:

```python
def export_legend(handles, name, ncol=1, figsize=(4, 1.5), fontsize=6, **kw):
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis('off')
    ax.legend(handles=handles, loc='center', frameon=False,
              ncol=ncol, fontsize=fontsize, handlelength=1.6,
              columnspacing=2.0, handletextpad=0.6, **kw)
    save_all(name, fig)
    plt.close(fig)
```

Published figures place the same legend differently depending on the layout —
a horizontal strip under the panels, two columns at the bottom, or a vertical block in
the right margin. Standalone export is what makes that free.

## 6. Triple-format export

```python
def save_all(base, fig=None, dpi=300, **kw):
    f = fig if fig is not None else plt.gcf()
    for d in ('pdf', 'svg', 'png'):
        os.makedirs(d, exist_ok=True)
    f.savefig(f'pdf/{base}.pdf', bbox_inches='tight', **kw)   # journal + assembly
    f.savefig(f'svg/{base}.svg', bbox_inches='tight', **kw)   # Illustrator editing
    f.savefig(f'png/{base}.png', dpi=dpi, bbox_inches='tight', **kw)  # preview
```

Why all three:
- **PDF** — what the journal accepts and what Illustrator places cleanly.
- **SVG** — friendlier for object-level editing in some tools; also what Figma imports.
- **PNG** — for Slack/email/Word drafts and for eyeballing without opening a vector app.

## 7. Single source of truth for data

Regenerate figures from the **published source-data file**, not from intermediate
model outputs.

```python
from pathlib import Path
HERE = Path(__file__).resolve().parent      # cwd-independent
SRC  = HERE.parent / 'source_data.xlsx'
df   = pd.read_excel(SRC, sheet_name='Fig2')
```

Consequences:
- The number in the figure, the number in the Source Data file, and the number in the
  text can never drift apart.
- Reviewers who recompute from Source Data reproduce the figure exactly.
- Satisfying the journal's Source Data requirement becomes free rather than a
  last-minute reconstruction.

If a derived quantity is computed in the plotting script, comment the definition
inline — reviewers do read these:

```python
# Panel c metric: cost increase (%) scaled by capacity to absorb it.
# Dividing by the *true* capacity means well-resourced units score low --
# that inversion is intended, and the caption says so.
df['ratio_metric'] = df['cost_increase_pct'] / df['capacity']
```

## 8. File-size management

The 50 MB per-figure cap is real, and vector scatter layers are the usual cause.

| Situation | Remedy |
|---|---|
| Scatter with n > ~5,000 | `ax.scatter(..., rasterized=True)` — marks become raster at 300 dpi, axes and text stay vector |
| High-resolution raster basemap | Downsample to the printed size at 300 dpi before placing |
| Many overlapping polygons (coastlines at full resolution) | Use `cfeature.COASTLINE.with_scale('110m')` instead of `'10m'` |
| Large heatmaps | `pcolormesh(..., rasterized=True)` |

`rasterized=True` is fully compatible with the mixed-figure rule: the data layer is
raster at 300 dpi, and the axes, ticks, labels, and annotations remain vector objects.

## 9. Assembly in a vector tool

**Illustrator** (preferred)
1. New document at 180 × H mm, RGB, 300 dpi effective.
2. `File > Place` each panel PDF; *do not* embed as raster.
3. Align to a grid; keep inter-panel gutters consistent (3–5 mm).
4. Add panel letters as live text in Arial bold 8 pt if not baked into the panels.
5. Place the legend file(s).
6. Save as `.ai` (working) and `.pdf` (submission).

**PowerPoint** (acceptable)
- Set slide size to 18 × H cm.
- Insert panels as PDF/EMF so they stay vector; never paste as picture.
- No drop shadows, no 3D, no bevel.
- Export as PDF.

**Never**: assemble in Word, or flatten in Photoshop.

Verify after assembly: open the final PDF, zoom to 800%, and confirm text edges stay
crisp and are selectable.

## 10. Icon libraries for schematics

System-topology and method-overview diagrams need a consistent icon vocabulary. Keep
them versioned alongside the figures:

```
figures/icons/
├── README.md          # provenance and licence of every icon
├── pv.svg    pv.png
├── wt.svg    wt.png
├── ess.svg   ess.png
├── chp.svg   chp.png
└── ...
```

Keep both SVG (for assembly) and PNG (for quick drafts). Record the licence of every
third-party icon in the README — the Third Party Rights form will ask.

## 11. Reproducibility

- Every figure regenerable by one command from a clean checkout.
- Scripts are `cwd`-independent (`Path(__file__).resolve().parent`).
- No manual post-hoc edits to *data* in the vector tool. Assembly may move and align
  panels; it may not change a number, a bar height, or a point position. If a value is
  wrong, fix the script and re-export.
- Pin the environment (`requirements.txt`) — matplotlib default changes between
  versions will silently alter the figure.

---

## 12. Pre-submission audit checklist

Run every item. Mark CRITICAL failures first.

### Specification
- [ ] Width is exactly 88 mm or 180 mm
- [ ] Height within the caption-dependent ceiling
- [ ] All text within 5–12 pt at final size, house target 9–10.5 pt body
- [ ] Axis labels, tick labels and legend text are the SAME size
      (panel letters ≤12 pt bold). See SKILL.md Step 0 for why this is not 5–7
- [ ] Arial or Helvetica throughout, including mathtext
- [ ] RGB colour mode (original research)
- [ ] Charts/maps/schematics exported as PDF/EPS/AI, not PNG/JPG
- [ ] Raster components ≥300 dpi, never upsampled
- [ ] Text and overlays editable, nothing flattened
- [ ] File under 50 MB
- [ ] `pdf.fonttype = 42` set

### House style
- [ ] Panel letters lowercase, bold, no parentheses, consistent position
- [ ] No `set_title()` on data panels
- [ ] Axis labels sentence case, units in parentheses, negative exponents
- [ ] Tick values in 0.1–999, or `useMathText=True`
- [ ] Top and right spines removed (or full box used consistently)
- [ ] Grid y-only, dashed, alpha ≤0.3
- [ ] Legend `frameon=False`, no legend title
- [ ] Inner panels have no duplicate axis labels
- [ ] Tick direction consistent across the whole paper

### Colour
- [ ] ≤6 saturated colours
- [ ] Semantic colours identical to every other figure in the paper
- [ ] Colour-blind safe; no red/green as the only distinction
- [ ] Dual encoding (colour + linestyle / marker / hatch)
- [ ] No `jet` / `rainbow`
- [ ] Diverging colormap centred on a meaningful zero
- [ ] Log norm used for long-tailed count data

### Honesty
- [ ] Axis ranges not truncated to exaggerate; breaks marked if used
- [ ] Error bars defined in the caption (SD / SE / CI) with n
- [ ] Distributions shown, not just means
- [ ] Clipped colour ranges shown with `extend='both'`
- [ ] Independent y-limits in small multiples disclosed in the caption
- [ ] Every number in the figure traceable to the source-data file

### Caption
- [ ] First sentence states the finding, not the setup
- [ ] Self-contained; all abbreviations defined
- [ ] 2–5 sentences
- [ ] Statistical tests, n, and error definitions stated

### Decoration
- [ ] No 3D, no drop shadow, no bevel, no meaningless gradient
- [ ] No chartjunk; every element earns its place — including the ones that are
      missing (reference line, colour bar, units, map layers: see SKILL.md Step 3d)
- [ ] Reference line present where a "good direction" exists
