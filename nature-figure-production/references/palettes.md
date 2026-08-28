# Palette gallery: worked colour schemes

`style.md` §9–13 gives the *rules* for colour. This file gives **worked examples** —
concrete, reusable schemes taken from published figures, each with the hex values, the
job it does, and the reason it works. Copy one and rename the keys; do not blend two.

Every lightness number quoted below is CIE L\* (0 = black, 100 = white), computed from
the hex values as printed. They are given because lightness — not hue — is what decides
whether a scheme survives greyscale printing and colour-vision deficiency, and because a
palette's claim to work should be checkable rather than asserted.

## Table of contents

1. How to choose from this file
2. Diverging ramps
3. Sequential ramps
4. Ordered class ramps (ordinal categories)
5. Qualitative sets
6. Semantic dictionaries
7. Two- and three-colour contrasts
8. Two-factor (2 x 2) encodings
9. Region fills and their marks
10. Neutrals and basemap tones
11. Checking a palette before committing to it

---

## 1. How to choose from this file

Four questions, in order. They are the same four that decide the colormap in
`style.md` §13, applied to discrete palettes as well.

1. **Is the variable continuous or categorical?** Continuous → §2 or §3.
   Categorical → §4 (if the categories have a rank) or §5 (if they do not).
2. **Does the variable have a meaningful midpoint** — zero, a break-even, a
   baseline year, a standard? Yes → diverging (§2). No → sequential (§3).
   A diverging ramp on a variable with no midpoint invents a boundary the data
   does not have, which is the single most common colour error in submitted figures.
3. **Is colour carrying a claim, or only an identity?** A claim ("these six
   regions rank from most to least feasible") needs an ordered ramp. An identity
   ("which country is this line") needs a qualitative set and is allowed more
   than six values, because the reader looks colours up rather than comparing them.
4. **How many layers does the panel have?** If two layers are both colour-coded —
   a choropleth under a point cloud, say — only one may be polychromatic. The other
   must be single-hue and quiet (§3, teal or grey). Two competing ramps in one panel
   is unreadable regardless of how good each one is.

**One paper, one system.** Pick a diverging ramp, a sequential ramp, and a
qualitative set at the start, put them in a shared module, and use those three
everywhere including the supplement. Figures that each pick their own palette read
as assembled by different people, which is exactly what reviewers infer.

---

## 2. Diverging ramps

For signed quantities, differences from a baseline, anomalies, residuals, and
gaps. Blue–red is the safe diverging axis: it survives the common forms of
colour-vision deficiency, which red–green does not.

### 2.1 Navy–red, 13 steps — the general-purpose diverging ramp

```python
DIVERGING = [
    '#012A61', '#015696', '#0B75B3', '#4596CD', '#89CAEA', '#BBE6FA',
    '#E2F4FE', '#F1EEED', '#FCCDC9', '#EE9D9F', '#DE6A69', '#C84747',
    '#982B2D',
]
```

L\*: 18.0, 35.7, 47.0, 59.4, 78.2, 89.0, **95.2, 94.3**, 86.3, 72.8, 58.8, 48.6, 35.2

Deep navy through near-white to deep brick. Thirteen steps is enough resolution to
build a smooth `LinearSegmentedColormap` for a continuous field, and enough
separation to slice into 6 or 12 discrete classes (§2.2, §4.2) that still belong to
the same family. This is the ramp to reach for on a residual map, an anomaly field,
a cost-difference surface, or a trajectory coloured by a signed value.

```python
import matplotlib.colors as mcolors
cmap = mcolors.LinearSegmentedColormap.from_list('diverging', DIVERGING, N=256)
```

**Two caveats, both checkable in the L\* numbers above.**

*The neutral is off-centre.* The visually neutral stop is `#F1EEED` at index 7 of
13, so with evenly spaced stops it lands at 7/12 ≈ 0.583, not 0.5 — a zero drawn
with `Normalize` will not be the palest colour. Either pin the stops:

```python
pos = [i / 7 * 0.5 for i in range(8)] + [0.5 + (i - 7) / 5 * 0.5 for i in range(8, 13)]
cmap = mcolors.LinearSegmentedColormap.from_list('diverging', list(zip(pos, DIVERGING)), N=256)
```

or leave the stops even and let `TwoSlopeNorm(vcenter=0)` carry the centring — but
do one of the two, deliberately.

*The ends are not equally heavy.* The navy end sits at L\* 18.0 and the brick end at
35.2, a 17-point gap, so negative values read as visually stronger than positive
values of the same magnitude. That is fine, and often desirable, when the argument is
about one direction (a deficit, a shortfall). It is misleading when the claim is that
the two directions are symmetric. In that case trim the darkest navy, or use §2.3.

### 2.2 Navy–red, 12 steps — cyclic and seasonal

```python
MONTHS = [
    '#012A61', '#015696', '#0B75B3', '#4596CD', '#89CAEA', '#BBE6FA',
    '#E2F4FE', '#F1EEED', '#FCCDC9', '#EE9D9F', '#DE6A69', '#C84747',
]
```

The same ramp truncated to twelve, for months of the year on a violin series, a
monthly small-multiple grid, or a per-month line family. Cold months land in the
blues and warm months in the reds, so the colour is not an arbitrary lookup — it
restates the variable the reader already has in mind, and the legend becomes
optional.

The honest limitation: a calendar is cyclic and this ramp is not, so December and
January sit at opposite ends. Accept it (readers tolerate the seam) or, if the
wrap matters to the claim, use `twilight` and say so in the caption.

### 2.3 Blue–cream–red, 5 steps — diverging with a warm midpoint

```python
DIVERGING_WARM = ['#012f48', '#669aba', '#fbf0d9', '#be1420', '#7a0101']
```

L\*: 18.0, 61.2, **95.1**, 40.5, 24.2

Endpoints within 6.2 L\* of each other, so the two directions carry equal weight —
the property §2.1 lacks. The cream midpoint (`#fbf0d9`) reads as a deliberate
neutral against a white page, where a white or near-white midpoint disappears into
the background and makes the mid-range of the data look like missing data. Use this
one on filled contours, choropleths and heatmaps, where the midpoint occupies real
area; §2.1 is better for point marks, where an almost-invisible neutral is harmless.

The alpha-suffixed variant of the same family layers a heatmap over a basemap
without hiding it:

```python
DIVERGING_WARM_A = ['#012f4830', '#669aba40', '#fbf0d950', '#be142060', '#7a010170']
```

Opacity rises with magnitude, so the extremes are the opaque cells and the
mid-range lets the basemap through. Prefer this to a global `alpha=` on the whole
layer, which fades the extremes just as much as the middle.

### 2.4 Red–yellow–blue, 8 steps — asymmetric resolution

```python
GAP = ['#d73221', '#e35235', '#e48070', '#fcb777', '#fde699',
       '#fef4ae', '#d2edf2', '#6491c1']
```

L\*: 48.1, 54.7, 64.2, 79.6, 91.6, **95.5**, 92.0, 58.8

Six stops on the red side, two on the blue. Deliberately asymmetric: the argument
is about how far short a case falls, so the failing range gets the resolution and
the succeeding range only needs to be distinguishable from it. Use this shape when
one tail is the finding and the other tail is context — a feasibility gap, an
exceedance, a budget overrun.

State the asymmetry in the caption. An unannounced non-linear colour scale is a
figure-integrity problem, not a design choice.

---

## 3. Sequential ramps

For magnitude with no meaningful midpoint. Single-hue sequentials are the safest
thing in this file: because lightness is monotone, they survive greyscale and every
form of colour-vision deficiency without modification.

### 3.1 One hue per physical quantity

```python
BLUES  = ['#c6dbef', '#6baed6', '#2171b5', '#084594']   # e.g. wind
GREENS = ['#c7e9c0', '#74c476', '#238b45', '#005a32']   # e.g. wave
REDS   = ['#fff5f0', '#fcbba1', '#fc9272', '#ef3b2c', '#99000d']   # e.g. heat demand
```

The pattern matters more than the hexes: when a figure shows the *same* magnitude
scale for several different resources, give each resource its own hue and vary
lightness within it. Then a reader who has learned "blue = wind" from panel **a**
can read the seasonal grid in panel **d** without a legend, and the shade still
reads as magnitude. Mixing resources into one rainbow throws that away.

Extend to more classes by taking a longer slice of the same ColorBrewer family
(`Blues`, `Greens`, `Reds`) rather than by inventing intermediate hexes by eye.

### 3.2 White–teal — the quiet second layer

```python
TEAL = ['#ffffff', '#cfe3e3', '#9fc8c8', '#5fa3a3', '#2f7a7a']
```

L\*: 100.0, 88.8, 77.8, 62.7, 46.9 — monotone, 53 L\* of range.

A muted single-hue ramp for the secondary colour-coded layer in a panel whose main
layer already uses a diverging ramp (§2). Teal is far enough from both ends of a
blue–red ramp that the two layers cannot be confused, and desaturated enough that
it does not compete for attention. Typical use: share-of-population or
percent-of-cases shown as a supporting choropleth under the diverging quantity that
carries the claim.

### 3.3 Borrowed sequentials

For rasters and building/terrain layers, a perceptually uniform matplotlib
colormap is better than anything hand-built: `viridis`, `magma`, `cividis`
(colour-blind optimised), or `YlOrBr` where a warm earth ramp suits the subject.
Hand-built ramps are worth the effort only when the palette has to match a
categorical scheme elsewhere in the paper.

---

## 4. Ordered class ramps (ordinal categories)

Discrete classes that have a rank. The ramp does the work the legend would
otherwise do: the reader can order the classes without reading their names.

### 4.1 Scenario or horizon ramp — one hue, three steps

```python
SCENARIO = {'2030': '#9ecae1', '2040': '#4292c6', '2050': '#08519c'}
```

Time horizons, stringency levels, or model generations. One hue, darkening with the
ordinal. Any reader immediately reads "later / stronger / more" from the darker
colour, and the scheme costs nothing in the qualitative budget of §5 — it consumes
one hue, not three.

The same trick generalises via `shade_ramp()` in `nature_style.py`:
`shade_ramp('#08519c', 3)` gives three lightness steps of any base hue.

### 4.2 Six ranked classes — the partition ramp

```python
CLASSES = ['#012A61', '#0B75B3', '#89CAEA', '#F0D2D2', '#DC5654', '#982B2D']
```

L\*: 18.0, 47.0, 78.2, **86.6**, 54.6, 35.2

A six-class slice of the §2.1 family, for an ordered partition — the six regions of
a two-threshold classification, six feasibility or risk bands, six deciles grouped.
Best classes run dark blue, worst run dark red, and the pale middle marks the
classes that are neither. This is the palette to hand to
`partition_legend()` in `nature_quadrant.py`.

**Check before you use it as-is.** The two middle classes sit at L\* 78.2 and 86.6,
only 8.4 apart, so they are nearly indistinguishable in greyscale and hard for a
reader with a blue-yellow deficiency. If the argument turns on telling those two
apart, either dual-encode them (hatch, marker, or a border) or widen the gap by
pulling the third stop down to `#4596CD`.

---

## 5. Qualitative sets

For categories with no rank. The ceiling from `style.md` §9 stands: **at most six
saturated colours** where colour carries a claim.

### 5.1 Journal-derived qualitative sets

```python
NPG  = ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F',
        '#8491B4', '#91D1C2', '#DC0000', '#7E6148', '#B09C85']
AAAS = ['#3B4992', '#EE0000', '#008B45', '#631879', '#008280',
        '#BB0021', '#5F559B', '#A20056', '#808180', '#1B1919']
NEJM = ['#BC3C29', '#0072B5', '#E18727', '#20854E', '#7876B1',
        '#6F99AD', '#FFDC91', '#EE4C97']
JAMA = ['#374E55', '#DF8F44', '#00A1D5', '#B24745', '#79AF97',
        '#6A6599', '#80796B']
```

Four qualitative sets reverse-engineered from the house styles of major journal
families. NPG is the default already exported as `ACADEMIC` in
`nature_style.py`; the other three are here because the choice of set is one of the
cheapest ways to give a paper a consistent identity that is not the matplotlib
default.

**Pick one set per paper and cycle it in order.** The order is part of the design —
the first two entries of each set are the strongest contrast pair, so a two-series
panel that takes entries 0 and 1 gets the best available separation for free.

### 5.2 When more than six is legitimate

Concatenating the four sets above gives ~35 distinguishable colours. That is
defensible only where colour is an **identity lookup**, not a comparison: fifty
countries' trajectories on a scatter, where the reader's question is "where is
Japan" and never "is orange bigger than teal". The tell is the legend — if it is
a searchable index rather than something to be memorised, the large set is doing an
index's job.

Even then: colour must not be the only channel carrying the identity. Direct-label
the handful of cases the text discusses and let the rest be an undifferentiated
context cloud, which is `style.md` §9 applied to a large-*n* panel.

---

## 6. Semantic dictionaries

One physical quantity, one colour, fixed for the whole paper. See `style.md` §10
for the rule; these are worked instances of it.

### 6.1 Cost components

```python
COST = {
    'Renewable Generation Cost':    '#4C72B0',   # blue
    'Energy Storage System Cost':   '#DDAA33',   # amber
    'Conventional Generation Cost': '#808080',   # grey
    'Sector-Coupling System Cost':  '#8172B3',   # purple
    'Penalty Cost of Curtailment':  '#d47d49',   # orange
    'Cost of Unserved Energy':      '#C44E52',   # red
}
```

Six components, the ceiling exactly. Note the deliberate choices inside it: the
conventional-generation term is **grey**, because it is the incumbent the figure is
arguing against and should recede; and the two penalty terms are warm, so a stacked
bar with visible warm blocks reads as "this configuration is failing" before the
reader has consulted the legend at all.

### 6.2 Technology and flow directions

```python
TECH = {
    'PV':           '#458933',
    'EV':           '#a4312a',
    'charge':       '#afd7ae',   # pale PV green: energy going in
    'discharge':    '#eaabaa',   # pale EV red:   energy coming out
    'grid_deficit': '#666666',
    'curtailment':  '#ffe675',
}
```

The paired trick: `charge` and `discharge` are pale versions of the `PV` and `EV`
hues, so a flow band is visibly a lighter relative of the asset it belongs to.
Two levels of a hierarchy in one channel, at no cost in the colour budget.

### 6.3 Vehicle or asset classes — two ways

```python
FLEET_A = {'ev': '#E64B35', 'taxi': '#4DBBD5', 'bus': '#00A087'}   # NPG 0,1,2
FLEET_B = {'taxi': '#E07B54', 'bus': '#4A90D9', 'ev': '#5BB56F'}   # softened
```

Same three categories, two valid schemes. `FLEET_A` takes the first three NPG
entries, which is what to do when these categories are the paper's main comparison
and should be its most saturated marks. `FLEET_B` desaturates the same red/blue/green
triad, which is what to do when the categories are drawn on top of a busy layer
(a map, a trajectory field) that full-saturation marks would fight with.

**Choose against the background, not in isolation.** Where these classes sit on a
tinted zone, the mark colour has to clear the zone colour by enough to survive being
shrunk — e.g. a `#FDAE61` mark over a `#FDDBC7` background band. Both are orange, and
12.4 L\* apart: enough that the legend swatch is never mistaken for the band behind
it, and about the minimum worth accepting. Check this pair explicitly, because it is
the one comparison a palette check on the *marks alone* will never make.

### 6.4 Renewable mix

```python
MIX = ['#A6CEE3', '#F5C518', '#1F9FB5']   # e.g. wind / solar / wave
```

Three colours for a small pie or a stacked share bar. Deliberately not three
saturated primaries: solar takes the one strongly saturated slot because it is
usually the quantity the panel is about, and the two blues sit either side of it.

---

## 7. Two- and three-colour contrasts

The most common colour decision in a paper, and the one most often made by accident.

```python
# Model vs measurement
COLOR_SIM      = '#d2352c'   # simulated / predicted
COLOR_REAL     = '#4a7db3'   # measured / observed
COLOR_BASELINE = '#333333'   # baseline, drawn dashed

# Sign of an effect: coefficients, links, flows
POSITIVE = '#0B75B3'
NEGATIVE = '#982B2D'

# Position relative to a fitted line or reference
ABOVE = '#0B75B3'
BELOW = '#DE6A69'

# Feasible vs not
FEASIBLE   = '#4C72B0'
INFEASIBLE = '#C44E52'

# Significance, applied per mark rather than as a series colour
SIGNIFICANT     = '#982B2D'   # p < 0.05
NOT_SIGNIFICANT = '#0B75B3'
```

All of these are endpoints of the §2.1 ramp, which is the point: a paper whose
two-colour contrasts are drawn from its diverging ramp has one colour system rather
than five, and a reader who has learned "navy is above, brick is below" from Figure 1
carries it into every later panel.

**Traffic-light thresholds** are the exception worth flagging:

```python
BAND = ['#009988', '#DD8452', '#C44E52']   # e.g. VIF < 5, 5-10, >= 10
```

Green–amber–red is instantly readable for most people and **not** colour-blind safe.
Use it only where the class is also stated in text or position (a sorted bar chart
where the red bars are all at one end), never as the sole encoding.

---

## 8. Two-factor (2 x 2) encodings

When two binary factors cross, do not spend four unrelated hues on them. Give
**hue to one factor and lightness to the other**, and the reader can decompose the
legend instead of memorising it.

```python
STATE = ['#FDAE61', '#BD0026', '#ABD9E9', '#2C7BB6']
LABELS = ['Parking, non-shaded', 'Parking, shaded',
          'Driving, non-shaded', 'Driving, shaded']
```

L\*: 77.3, 39.5 (warm pair) | 84.1, 49.6 (cool pair)

Warm = parking, cool = driving; light = non-shaded, dark = shaded. Each pair is
separated by 35–38 L\*, so the shading factor survives greyscale on its own, and the
two hue families are on the blue–orange axis, which is the colour-blind-safe one.
Both factors are recoverable independently — which is exactly what a 2 x 2 legend
should let a reader do, and what four arbitrary hues prevent.

Order the legend so the factorial structure is visible: group by the hue factor,
step lightness within each group.

---

## 9. Region fills and their marks

For region plots (`quadrant.md`), a filled background classifier needs marks drawn on
top of it. The failure mode is marks that vanish into their own region.

```python
REGION_FILL = {'Q1': '#d5e8f1', 'Q2': '#a9d9bb', 'Q3': '#f6dfd6', 'Q4': '#cfcce3'}
REGION_MARK = {'Q1': '#4a9cc7', 'Q2': '#5ab87a', 'Q3': '#c07060', 'Q4': '#8a85b0'}
```

Fills L\*: 90.9, 82.7, 90.4, 82.9 — a span of 8.2, i.e. deliberately near-uniform.
Marks L\*: 61.1, 67.9, 55.7, 57.4.

Two properties, both verifiable from those numbers:

1. **The fills are all equally quiet.** Because they sit within 8 L\* of each other,
   no region looks more important than another. A partition background that varies
   in weight silently argues that one region matters more, which is a claim the
   classifier is not making.
2. **Every mark clears every fill.** The mark is the same hue as its region at
   higher saturation and lower lightness — gaps of 29.8, 14.8, 34.7 and 25.5 L\*
   within each pair. So a mark is always identifiable as belonging to its region
   *and* always visible against it.

Keep fill alpha low (0.15–0.25) if anything else is drawn underneath, and note that
the paler variant `'Q3_BELOW': '#e8c0b0'` exists for the case where one region has
to be split by a second criterion — same hue again, one step darker.

Where the regions are ranked rather than merely distinct, use §4.2 instead: ranked
partitions want an ordered ramp, not four independent hues.

---

## 10. Neutrals and basemap tones

Everything that is present so the reader can orient themselves but encodes no
variable.

```python
GREY = {
    'land':  '#E8E8E8',   # filled land, when land must read as a surface
    'fill':  '#F2F2F2',   # panel-internal fills, zone bands
    'line':  '#888888',   # coastlines, borders
    'faint': '#AAAAAA',   # graticule, secondary reference lines
    'text':  '#404040',   # annotation text; softer than pure black
    'dark':  '#333333',   # baselines, zero lines
}
```

Two habits worth copying:

- **Land at `#CECECE` with `alpha=0.2`** rather than a flat mid-grey. The basemap is
  a large amount of ink encoding nothing, and it will beat the marks unless actively
  suppressed (`maps.md`).
- **`#404040` for annotation text, not `#000000`.** Pure black annotation competes
  with the data marks; a dark grey reads as a label layer sitting behind them. Axis
  and tick text stay black.

Zone shading takes its own light triad, at `alpha` 0.10–0.20 with `zorder=0`:

```python
ZONES = [(0, 8, '#ABD3A0', 'Off-peak'), (8, 17, '#FBEA2E', 'Mid-peak'),
         (17, 21, '#EC3E31', 'Peak'),   (21, 24, '#ABD3A0', 'Off-peak')]
```

---

## 11. Checking a palette before committing to it

Run these four before the palette propagates through twenty figures. Each is
cheap, and each catches a failure that is expensive to fix late.

**1. Greyscale.** Convert to L\* and check that categories which must be
distinguished differ by more than ~10 points.

```python
import matplotlib.colors as mcolors

def lightness(hex_color):
    """Approximate CIE L* of a hex colour."""
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in mcolors.to_rgb(hex_color))
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return 116 * (y ** (1 / 3) if y > 0.008856 else 7.787 * y + 16 / 116) - 16

print([round(lightness(c), 1) for c in DIVERGING])
```

**2. Colour-vision deficiency.** Blue–red and blue–orange survive; red–green does
not. If a red–green pair is unavoidable, dual-encode with linestyle, marker or hatch
so colour is never the only channel.

**3. Print size.** View the palette at the panel's *placed* width, not at the size
it renders on screen. Distinctions that hold at 180 mm routinely collapse at 45 mm,
and thin lines lose saturation faster than filled areas do.

**4. Count the saturated colours.** More than six carrying a claim means the figure
is asking the reader to hold more than they can. Split the panel, aggregate the
categories, or move the extras into a grey context layer.
