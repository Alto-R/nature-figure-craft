<div align="center">

# nature-figure-craft 📐

**Research figures are two problems, not one: which chart to draw, and how to draw it so it survives submission.**

Two installable Claude Code skills, plus three plotting modules that work on their own.

![Skills](https://img.shields.io/badge/skills-2-4C72B0)
![Python](https://img.shields.io/badge/python-3.9%2B-3C5488)
![matplotlib](https://img.shields.io/badge/matplotlib-%E2%89%A53.5-0B75B3)
![R](https://img.shields.io/badge/R-circlize-982B2D)
![License](https://img.shields.io/badge/license-CC--BY--4.0-00A087)
![Status](https://img.shields.io/badge/status-v0.1%20first%20release-DDAA33)

**[中文](README.md)** | **[English](README-EN.md)**

</div>

---

## 🙋 About

I'm [Churui Huang](https://alto-r.github.io/), a postgraduate at Peking University working on smart cities, urban computing and energy systems.

This is what accumulated from my own submissions: the palettes, the layout rules, the map layer ordering, how a region plot's dividing lines get justified, the render-panels-separately-then-assemble pipeline — most of it comes from figures I actually drew for manuscripts.

**It keeps growing.** Every new paper and every new batch of figures adds whatever I got wrong and whatever rule came out of it — `palettes.md` in particular is meant to thicken over time.

This is **v0.1, the first release**. Issues pointing out what's wrong are welcome.

---

<div align="center">

| | | |
|:--:|:--:|:--:|
| [🧭 What this is](#-what-this-is) | [⚖️ Division of labour](#-division-of-labour) | [🚀 Install](#-install) |
| [🗂️ Layout](#-layout) | [🎨 Palette gallery](#-palette-gallery) | [🧩 Using the style module alone](#-using-the-style-module-alone) |
| [💡 The short version](#-the-short-version) | [📄 License](#-license) | |

</div>

---

## 🧭 What this is

Most bad figures are not badly *rendered* — they are badly *chosen*. A beautifully styled grouped bar chart of a time series is still the wrong figure. So the work is split in two, one skill each:

- **`chart-type-chooser`** — used *before* any plotting code. It profiles the data first, then asks what one sentence the figure has to make the reader remember, and returns two or three candidate chart types, the rejected alternatives *with reasons*, an encoding plan, and an anti-pattern check. Covers ~70 chart types across nine communicative intents.
- **`nature-figure-production`** — used *after* the chart type is fixed. It applies the Nature-family final-artwork specification (88/180 mm column widths, landed type sizes, editable vector, RGB, 50 MB cap) and house style, adds recipes for the three chart families that carry their own geometry (maps, region plots, chord diagrams), and runs the real production pipeline: panels rendered separately, legends exported standalone, assembly in a vector tool.

Neither makes the scientific judgement for you. They handle the part after it — getting that judgement onto the page reliably.

## ⚖️ Division of labour

| | `chart-type-chooser` | `nature-figure-production` |
|---|---|---|
| **Answers** | *Which* chart | How to make it publication-grade |
| **Input** | One sentence the reader should remember + data structure | A chosen chart type + data |
| **Output** | 2–3 candidates + reasons + rejected options + encoding plan | Sizes, style code, exported artwork, submission audit |
| **When** | **Before** writing any plotting code | **After** the chart type is settled |

> Standard order: `chart-type-chooser` → `nature-figure-production`.

## 🚀 Install

Copy into your Claude Code skills directory:

```bash
git clone https://github.com/Alto-R/nature-figure-craft.git
cd nature-figure-craft
cp -r chart-type-chooser        ~/.claude/skills/
cp -r nature-figure-production  ~/.claude/skills/
```

Windows:

```bat
xcopy /E /I chart-type-chooser        %USERPROFILE%\.claude\skills\chart-type-chooser
xcopy /E /I nature-figure-production  %USERPROFILE%\.claude\skills\nature-figure-production
```

After that just ask normally — "plot this for me", or "this figure doesn't look like a paper figure" — and the skills trigger themselves.

## 🗂️ Layout

```
nature-figure-craft/
│
├── chart-type-chooser/                 # skill 1: choosing
│   ├── SKILL.md
│   ├── references/
│   │   ├── catalog.md                  # nine intents x ~70 chart types
│   │   ├── decision-rules.md           # structure gates, encoding-channel ranking, tie-breaks
│   │   └── antipatterns.md             # symptom -> cause -> prescription
│   └── assets/
│       └── profile_data.py             # data profile: column types, group sizes, open vs settled decisions
│
└── nature-figure-production/           # skill 2: drawing
    ├── SKILL.md
    ├── references/
    │   ├── spec.md                     # final-artwork spec (88/180 mm, landed type, vector, 50 MB)
    │   ├── style.md                    # typography, units, colour rules, colormap selection
    │   ├── palettes.md                 # palette gallery (below)
    │   ├── composition.md              # ten multi-panel layout templates
    │   ├── quadrant.md                 # region plots: where dividers come from, naming, layers, legend
    │   ├── maps.md                     # map panels: layer stack, basemap presets, points vs polygons
    │   └── workflow.md                 # panel-separated pipeline + pre-submission checklist
    └── assets/
        ├── nature_style.py             # panel() / apply_style() / landed_report() / save_all()
        │                               #   + every palette constant, diverging_cmap(), palette_report()
        ├── nature_map.py               # five map layers: basemap / polygons / field / points / marginals
        ├── nature_quadrant.py          # region plots: thresholds / backgrounds / bubbles / insets / legend
        └── nature_chord.R              # chord diagrams (circlize): opacity-encoded flow, vector export
```

Three of the assets carry their own self-test on synthetic data — run them and you get demo figures:

```bash
python nature_style.py      # demo panel + palette health report
python nature_quadrant.py   # demo_quadrant.png / _legend.png / _2x2.png
Rscript nature_chord.R      # demo_chord_ungrouped.* / _grouped.* / _legend.pdf
```

> `nature_map.py` has no self-test — it needs cartopy and real coordinates, and there is no meaningful synthetic example to build.

## 🎨 Palette gallery

`references/palettes.md` is a set of **copy-ready** colour schemes, each with the job it does and the reason it works, all exported as constants from `nature_style.py`:

| Kind | Constants | Where it goes |
|---|---|---|
| Diverging | `DIVERGING` (13-step), `DIVERGING_WARM`, `DIVERGING_GAP` | Signed quantities, anomalies, residuals, differences from a baseline |
| Sequential | `SEQ_BLUE` / `SEQ_GREEN` / `SEQ_RED` / `SEQ_TEAL` | One hue per physical quantity; teal reserved for the quiet second layer |
| Ordinal | `CLASSES6`, `SCENARIO` | Ranked categories, so the colour itself encodes rank |
| Qualitative | `NPG` / `AAAS` / `NEJM` / `JAMA` | Unranked categories — pick one set per paper |
| Semantic | Cost / technology / fleet example dicts | One physical quantity, one colour, fixed for the whole paper |
| 2 × 2 | `TWO_FACTOR` | Two crossed binary factors: hue carries one, lightness the other |
| Region | `REGION_FILL` / `REGION_MARK` | Quadrant backgrounds and the marks that sit on them, given as pairs |

Every scheme comes with measured CIE L\* values rather than "looks about right":

```python
from nature_style import DIVERGING, diverging_cmap, CLASSES6, palette_report

cmap = diverging_cmap()                          # neutral pinned to 0.5, not the default 0.583
palette_report(CLASSES6, ordered=True)           # names the steps that collide in greyscale
```

## 🧩 Using the style module alone

No skill install needed — just drop `nature_style.py` into your project:

```bash
cp nature-figure-production/assets/nature_style.py  your_project/figures/
cd your_project/figures && python nature_style.py     # self-test, writes demo figures
```

```python
from nature_style import panel, apply_style, landed_report, save_all, clean_axes, panel_letter

p = panel(placed_mm=60, aspect=0.8)      # where this panel LANDS, not how big to draw it
apply_style(p)
fig, ax = plt.subplots(figsize=p.figsize)
...
clean_axes(ax)
panel_letter(ax, 'a')
landed_report(fig, p)                    # measure the landed type before exporting
save_all('fig1_a_timeseries', fig)       # writes pdf/ svg/ png/ together
```

The load-bearing idea: **fix type size by what it measures on the printed page, not by how big the script happens to draw it.** A real main figure is 10–25 panels placed at different widths, so there is no single `figsize` to use. What is invariant is the arithmetic — `landed_pt = drawn_pt × (placed_mm / drawn_mm)`. `panel()` does it; `landed_report()` verifies it against the actual text objects in the figure, which is where out-of-spec type always hides.

## 💡 The short version

**On appearance**
> Pin the hard spec first → push everything unimportant into grey → spend saturation on one or two things → delete freely (titles, frames, gridlines, legend boxes, repeated axis labels) → then go back and *add*: reference lines, units, n, colour bars, map layers. A figure has two failure modes, cluttered and bare, and only the first one is visible to a checklist.

**On choosing**
> Write down the one sentence the figure should make a reader remember. If you cannot write it, do not draw the figure.

## 📄 License

[CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

---

<div align="center">
<sub>Specifications come from journals' published artwork guidelines; the judgement calls are mine and represent no journal's official position.</sub>
</div>
