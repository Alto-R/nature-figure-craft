# House style: typography, axes, colour

The spec gets a figure through production. This layer is what makes it *read* as a
journal figure. Every rule here is recoverable from published Nature-family artwork.

Colour is covered here as *rules* (§9–13). For ready-to-copy schemes — a diverging
ramp, an ordinal class ramp, four qualitative sets, semantic dictionaries, 2×2
encodings, region fills — see **[palettes.md](palettes.md)**.

## Table of contents

1. Panel letters
2. Titles and captions
3. Axis labels and units
4. Tick values and scientific notation
5. Spines, grid, ticks
6. Legends
7. Multi-panel shared labels
8. Reference lines
9. Colour: emphasis has to be spent, not spread
10. Semantic colour dictionaries
11. Ready-made palettes
12. Shade variants and hatching
13. Colormap selection
14. Marks: separation, size, over-plotting
15. Zone shading
16. Time axes

---

## 1. Panel letters

Nature style is **lowercase, bold, no parentheses**, tight to the top-left of the axes.

```python
for i, ax in enumerate(axes.flat):
    ax.text(-0.14, 1.06, chr(97 + i), transform=ax.transAxes,
            fontsize=8, fontweight='bold', va='top', ha='left')
```

`(a)` with parentheses, and centred-below placement, are IEEE / Elsevier conventions.
Pick one convention and never mix within a paper.

Always position with `transform=ax.transAxes` so the letter stays put when data
ranges change. Hide unused grid slots with `ax.set_visible(False)`.

## 2. Titles and captions

- **Data panels carry no `set_title()`.** The caption is the title.
- A short label above a sub-panel identifying *which variable* it shows is an
  annotation, not a title, and is fine (e.g. `Renewable Generation Cost`).
- Caption discipline (this is where most figures lose reviewers):
  - **The first sentence states the finding, not the setup.**
    Bad: "Figure 5: Results on BIRD."
    Good: "Figure 5: Our method outperforms all baselines on BIRD across model sizes,
    with the largest gains on complex multi-table queries."
  - Self-contained: figure + caption alone must be understandable.
  - Define every abbreviation used inside the figure.
  - Two to five sentences. A caption that must run 300 words signals a figure trying
    to do too much.
  - State what error bars are (SD / SE / CI) and the n.

## 3. Axis labels and units

- **Sentence case**: `Power output (MW)`, not `Power Output (MW)`.
- **Units in parentheses**, always present.
- **Negative exponents, not slashes** — the strongest Nature-family fingerprint:

```python
ax.set_ylabel(r'Cost (USD kWh$^{-1}$)')       # not USD/kWh
ax.set_ylabel(r'Mean per-capita cost (USD capita$^{-1}$)')
ax.set_ylabel(r'Emission (g km$^{-1}$)')
ax.set_xlabel(r'CO$_2$ concentration (ppm)')
```

Use raw strings `r'...'` with `$...$` for mathtext, and set the mathtext font to match
the body font (see the style block in SKILL.md), otherwise `$^{-1}$` renders in
DejaVu while the label renders in Arial — a subtle but very visible mismatch.

## 4. Tick values and scientific notation

Keep tick numbers in the range **0.1 – 999**. First remedy is always a unit change
(kWh → MWh, W → kW, USD → thousand USD).

Only when no natural larger unit exists:

```python
ax.ticklabel_format(style='sci', axis='y', scilimits=(-3, 3), useMathText=True)
```

`useMathText=True` is mandatory — it renders `×10ⁿ` instead of the amateur-looking
`1e-3`.

Percentages:

```python
import matplotlib.ticker as ticker
ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))   # 0-1 -> 0%-100%
```

Tick density: use `ticker.MaxNLocator(nbins=4)` on small panels. Matplotlib defaults
produce cluttered ticks in small multiples.

## 5. Spines, grid, ticks

```python
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', linestyle='--', linewidth=0.4, alpha=0.3, zorder=0)
ax.xaxis.grid(False)
ax.tick_params(axis='both', length=2.5, width=0.6)
```

- Two-spine (left + bottom) is the default for bar and line charts.
- Full box is acceptable for heatmaps, matrices, and scatter panels with shaded regions.
- Maps: the frame is a judgement call, not a rule. `map_axes(frame=True)` is the
  default and draws a hairline outline, which gives the panel a defined edge and
  keeps the continents from floating in whitespace beside framed neighbours. Drop it
  (`frame=False`) when the map is an inset inside another panel, or when every other
  panel in the figure is frameless and the odd frame would read as a box around one
  thing. An earlier version of this file said to remove the frame unconditionally;
  that was over-generalised from one figure.
- Tick direction (`'in'` or `'out'`) is a free choice, but must be identical across
  every figure in the paper.

## 6. Legends

```python
ax.legend(frameon=False, fontsize=6)                       # standard
ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15),
          ncol=4, frameon=False, fontsize=6)               # many series, above axes

handles, labels = ax.get_legend_handles_labels()           # shared across panels
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, -0.02),
           ncol=3, frameon=False, fontsize=6,
           handlelength=1.6, columnspacing=2.0, handletextpad=0.6)
```

Rules: `frameon=False` always; no legend title; label only what matters; one shared
legend for a multi-panel figure rather than one per panel.

For real production figures, export the legend as a **separate file** so it can be
placed freely during assembly — see `workflow.md`.

## 7. Multi-panel shared labels

Only the outer ring of a grid carries axis labels.

```python
for i, ax in enumerate(axes.flat):
    row, col = divmod(i, n_cols)
    if col > 0:
        ax.set_ylabel(''); ax.set_yticklabels([])
    if row < n_rows - 1:
        ax.set_xlabel(''); ax.set_xticklabels([])

fig.supylabel(r'Mean per-capita cost (USD capita$^{-1}$)', fontsize=7, x=0.005)
plt.subplots_adjust(wspace=0.08, hspace=0.30)
```

`hspace >= 0.3` for stacked panels — the 0.2 default causes label collisions.
Call `plt.tight_layout()` first, then `subplots_adjust()` for fine control.

## 8. Reference lines

Almost every well-designed panel contains a line that tells the reader which
direction is "good". It converts a cloud of marks into a judgement.

| Line | Meaning | Code |
|---|---|---|
| Zero line | sign of an effect | `ax.axhline(0, lw=0.8, color='#333', ls='--')` |
| 1:1 diagonal | predicted vs observed | `ax.plot(lim, lim, 'k--', lw=0.8)` |
| Break-even diagonal | feasible vs infeasible | `ax.plot(x, x, ls='--', color='#d62728', lw=1.0)` |
| Median cross | above/below typical | `ax.axvline(med, ls='--', lw=0.8, color='#333')` |
| Threshold band | policy or physical limit | `ax.axhspan(lo, hi, color='grey', alpha=0.12, zorder=0)` |

Draw reference lines with `zorder` below the data, in dark grey or a single accent
colour, dashed, and thin.

## 9. Colour: emphasis has to be spent, not spread

A figure can only emphasise a few things at once. Decide which elements the reader
should reach first, and give the rest less visual weight — through saturation,
line weight, opacity, or `zorder`, whichever suits the chart.

If seven methods are compared, do not give all seven equal visual weight; the reader
cannot track that many. Pick the ones the figure is arguing about and let the rest
recede. If the highlighted series does not actually win, do not highlight it anyway —
that reads as manipulation.

Ceiling: **six saturated colours**. Beyond that humans lose track.

There is no house rule about *which* colours do the receding. Muted neutrals are one
common way and the `GREY` dict in `nature_style.py` is there if you want it, but a
desaturated hue, a lighter shade of the same colour, or lower opacity all work. What
matters is that the hierarchy exists and is consistent across the paper, not that any
particular part of the figure is grey.

## 10. Semantic colour dictionaries

Assign one colour per physical quantity, once, at the top of a shared module, and use
it in every figure of the paper including the supplement.

```python
COST = {
    'Renewable Generation Cost':    '#4C72B0',   # blue
    'Energy Storage System Cost':   '#DDAA33',   # amber
    'Conventional Generation Cost': '#808080',   # grey
    'Sector-Coupling System Cost':  '#8172B3',   # purple
    'Penalty Cost of Curtailment':  '#d47d49',   # orange
    'Cost of Unserved Energy':      '#C44E52',   # red
}

TECH = {
    'PV':           '#458933',
    'EV':           '#a4312a',
    'charge':       '#afd7ae',
    'discharge':    '#eaabaa',
    'grid_deficit': '#666666',
    'curtailment':  '#ffe675',
}
```

Payoff: after Figure 1 the reader has internalised the code, and every later panel is
readable without consulting the legend. This is the cheapest available source of
"this looks like a real paper".

Ordinal categories deserve an **ordered** ramp rather than arbitrary hues, so the
colour itself encodes rank and the reader can order the classes without reading their
names:

```python
CLASSES6 = ['#012A61', '#0B75B3', '#89CAEA', '#F0D2D2', '#DC5654', '#982B2D']
```

Dark blue (best) → pale blue → pale red → dark red (worst) — a six-class slice of the
`DIVERGING` family in §11, so a paper's class ramp and its continuous ramp are visibly
relatives. More worked semantic and ordinal schemes: [palettes.md](palettes.md) §4, §6.

## 11. Ready-made palettes

The three below cover most panels. **[palettes.md](palettes.md)** is the full gallery
— diverging, sequential, ordinal, qualitative, semantic, 2×2, and region fills, each
with the job it does and the measured lightness that makes it check out. All of them
are importable from `nature_style.py`.

```python
# General multi-series (Nature/Science flavour), cycle in order, max 6
ACADEMIC = ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4']

# Diverging: signed quantities, anomalies, residuals. Blue-red is the CVD-safe axis
DIVERGING = ['#012A61', '#015696', '#0B75B3', '#4596CD', '#89CAEA', '#BBE6FA',
             '#E2F4FE', '#F1EEED', '#FCCDC9', '#EE9D9F', '#DE6A69', '#C84747',
             '#982B2D']

# Two-series contrast
COLOR_SIM      = '#d2352c'   # simulated / predicted
COLOR_REAL     = '#4a7db3'   # measured / observed
COLOR_BASELINE = '#333333'   # baseline, dashed
```

`DIVERGING`'s neutral is the eighth of thirteen stops, so evenly spaced stops put it
at 0.583 rather than 0.5 and zero is not the palest colour. Build it with
`diverging_cmap()`, which pins the neutral, or centre it with `TwoSlopeNorm`.

Colour-vision deficiency affects roughly 8% of men and 0.5% of women. Prefer
ColorBrewer qualitative sets or the palettes above, and **dual-encode**: colour plus
linestyle, marker shape, or hatch, so the figure survives greyscale printing.
`palette_report()` reports the CIE L\* of every entry and names the pairs that
collide in greyscale — run it once, when the palette is chosen, rather than
discovering the collision in proof.

## 12. Shade variants and hatching

Same-hue layering for sub-categories:

```python
import matplotlib.colors as mcolors

def lighten(hex_color, f):
    """f=0 original, f=1 white"""
    return tuple(c + (1 - c) * f for c in mcolors.to_rgb(hex_color))

def darken(hex_color, f):
    """f=0 original, f=1 black"""
    return tuple(c * (1 - f) for c in mcolors.to_rgb(hex_color))

shades = [lighten('#3C5488', k) for k in (0.0, 0.35, 0.65)]
```

Hatching, for greyscale-safe sub-categories:

```python
ax.bar(x, y, color=lighten('#3C5488', 0.3), hatch='///',
       edgecolor='#666', linewidth=0.8)
```

Rules: hatch colour comes from `edgecolor` (`'#666'` reads well); at most 3 hatch
types per figure; colour is the primary channel and hatch is supplementary.

## 13. Colormap selection

| Data character | Colormap | Norm |
|---|---|---|
| Diverging around zero (differences, anomalies) | `RdBu_r`, `seismic` | `TwoSlopeNorm(vcenter=0)` |
| Probability / ratio 0–1 | `RdYlBu_r` | `Normalize(0, 1)` |
| Counts / density, long-tailed | `Blues`, `inferno` | **`LogNorm`** |
| Cost / benefit | `RdYlGn` | `Normalize` |
| Space–time heatmap | `Spectral_r` | `Normalize` |
| Generic sequential, perceptually uniform | `viridis`, `magma`, `cividis` | `Normalize` |

Never use `jet` or `rainbow`: perceptually non-uniform, invents false boundaries, and
is unreadable for colour-blind readers. `cividis` is the colour-blind-optimised
sequential default.

Clip extremes honestly: set `vmin`/`vmax` to data percentiles (e.g. 5th/95th) and use
`extend='both'` on the colorbar so clipping is visible rather than hidden.

```python
cb = fig.colorbar(sc, cax=cax, orientation='horizontal', extend='both')
cb.set_label(r'LCOE increase (USD kWh$^{-1}$)', fontsize=6)
cb.ax.tick_params(labelsize=5)
```

## 14. Marks: separation, size, over-plotting

White separation keeps dense marks legible:

```python
ax.bar(x, y, edgecolor='white', linewidth=0.3)                     # stacked bars
ax.scatter(lon, lat, s=14, edgecolors='white', linewidths=0.2)     # dense point map
```

Draw order matters — plot small values first so extremes sit on top:

```python
order = df[col].abs().argsort().values
d = df.iloc[order]
```

Over-plotting remedies, in order of preference:
1. `hexbin` or 2D KDE (n > 10,000)
2. `alpha=0.2` plus `rasterized=True`
3. Random subsample, stated in the caption

Bubble size must encode **area**, not radius:

```python
s = 20 + 480 * (value - vmin) / (vmax - vmin)   # matplotlib s is area in pt^2
```

## 15. Zone shading

Background bands for logical partitions (peak/off-peak, weekday/weekend, regimes):

```python
zones = [(0, 8, '#ABD3A0', 'Off-peak'),
         (8, 17, '#FBEA2E', 'Mid-peak'),
         (17, 21, '#EC3E31', 'Peak'),
         (21, 24, '#ABD3A0', 'Off-peak')]
for start, end, color, label in zones:
    ax.axvspan(start, end, facecolor=color, alpha=0.15, zorder=0, edgecolor='none')
```

Rules: `alpha` 0.10–0.20; `zorder=0`; `edgecolor='none'`.

## 16. Time axes

A 168-hour (weekly) axis labelled by day, with alternating day shading:

```python
def apply_weekly_style(ax, x_unit='hour'):
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    step = 24 if x_unit == 'hour' else 1440
    ax.set_xlim(0, step * 7)
    ax.set_xticks([d * step + step // 2 for d in range(7)])
    ax.set_xticklabels(days)
    for d in range(7):
        if d % 2:
            ax.axvspan(d * step, (d + 1) * step, facecolor='lightgray',
                       alpha=0.2, zorder=0, edgecolor='none')
    ax.axhline(0, color='black', linewidth=0.8, alpha=0.5)
    ax.yaxis.grid(True, linestyle='--', alpha=0.3, zorder=0)
    ax.xaxis.grid(False)
```

The same pattern generalises: label the *meaningful* unit (day, month, season) at
band centres rather than showing raw hour indices.
