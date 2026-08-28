# Panel recipes: the data-panel families that recur

`maps.md`, `quadrant.md` and the chord recipe cover the three families whose
**geometry** defeats a generic styling pass. This file covers the rest — the
panels that appear in almost every quantitative paper. Their trap is not
geometry. It is a small number of decisions that are easy to get subtly wrong,
invisible in the rendered panel, and expensive to discover at review.

Each recipe below states the decision, the failure it prevents, and the call in
`assets/nature_panels.py` that implements it. Copy the reasoning, not just the
code: the code is one defensible default, and a paper often needs a different
one — deliberately.

## Table of contents

1. Which recipe, and what every one of them shares
2. Distributions
3. Coefficients and effect sizes
4. Uncertainty: intervals, not asterisks
5. Compositions
6. Grouped comparisons
7. Relationships: the fit and its band
8. Too many points: density panels
9. State over time
10. Matrices
11. Flow panels (Sankey / alluvial)
12. Small-multiple grids
13. Panel audit

---

## 1. Which recipe, and what every one of them shares

`chart-type-chooser` decides *which* chart. This file assumes that decision is
made and asks how to draw it so it survives review. The map from claim to
recipe:

| The panel's claim | Recipe | Call |
|---|---|---|
| "These groups have different distributions" | §2 | `violin_box` |
| "These predictors matter, and by how much" | §3 | `forest` |
| "This total is made of these parts" | §5 | `stacked_bars` |
| "These conditions differ by this much" | §6 | `grouped_bars` |
| "x predicts y" | §7 | `fit_line` |
| "x predicts y, and there are 40,000 points" | §8 | `density_field` |
| "This series behaves differently under this regime" | §9 | `runs` + `state_bands` |
| "These variables covary like this" | §10 | `matrix_panel` |
| "Units moved between these classes" | §11 | plotly / R, legend in matplotlib |

**Four properties every recipe here enforces.** They are the ones a reviewer
checks, in the order they check them:

1. **The spread is drawn, or `n` is stated.** A bare mean is the most common
   way a panel claims more than the data supports. Every function in the
   module either takes an interval or can print `n`.
2. **The reference is drawn.** Zero, the 1:1 line, the baseline, the
   break-even. A panel with no reference asks the reader to bring their own,
   and they will bring the wrong one (`style.md` §8).
3. **The order is fixed and shared.** Categories keep one order across every
   panel of a grid and across the paper. A grid whose panels each sort
   themselves cannot be read across, which is the only reason to draw a grid.
4. **Data-derived text is in the script; everything else is not.** `R²`, `n`,
   a bar-top value and a fitted slope all move when the data moves, so they
   belong in code (`stat_box`). Callouts, arrows and prose do not, and are
   added at assembly (SKILL.md Step 4).

---

## 2. Distributions

A violin is a kernel density estimate, and a kernel density estimate is a
model with a smoothing parameter. Drawn on its own it hides the two things a
reader needs in order to discount it: the sample size and the actual
quartiles.

```python
from nature_panels import violin_box
summaries = violin_box(ax, [g1, g2, g3], colors=RAMP, spec=p,
                       labels=["Low", "Mid", "High"], show_n=True)
```

**Three departures from `ax.violinplot` defaults, and why each one matters.**

*Whiskers are redrawn at Tukey 1.5 × IQR, not at the extrema.* Matplotlib's
default `showextrema` bars run to the data minimum and maximum, so their length
grows with sample size. Two groups drawn from the same distribution get
visibly different violins purely because one has more points, and that
difference reads as a finding.

*The IQR box is white, drawn on top.* Colour is already carrying the group. A
second colour inside the violin makes the reader look for a second variable
that is not there.

*The median is a heavier tick than the box outline.* It is the number the
caption quotes, so it should be the mark the eye lands on.

**`show_n` is not optional when groups are unbalanced.** A violin over n = 9
is drawn exactly as wide and as smooth as one over n = 300, and it is the most
misleading mark in routine use. `violin_box` prints bare digits under the
category — measured first, and dropped with a warning if they will not fit,
because overlapping counts are worse than counts in the caption. Whichever way
they are reported, the caption says the second line is *n*.

**When not to use a violin.** Below roughly n = 20 per group the density
estimate is drawing the bandwidth rather than the data: use a box plot, or
plot the points directly. Above about eight groups the violins get too narrow
to read and a ridgeline or a small-multiple grid is the better form.

---

## 3. Coefficients and effect sizes

```python
from nature_panels import forest
forest(ax, names, beta, ci_lo, ci_hi, spec=p, order=CANONICAL_ORDER)
```

**Pass interval bounds, not error distances.** `matplotlib`'s `xerr` wants
distances from the estimate; `conf_int()` returns bounds. Feeding bounds
straight into `xerr` is the single most common silent error in this chart — the
bars still render, they are simply wrong, and an asymmetric interval hides it
well. `forest` takes bounds, converts them, and raises if `lo > hi`.

**Standardise before comparing.** Raw coefficients on variables with different
units are not comparable lengths, so a panel that puts them on one axis is
comparing units. Standardised β, elasticities, or per-IQR effects all work;
say which in the axis label.

**Fix the row order once, and share it.** `order=` takes an explicit sequence.
For a grid of models, pass the *same* sequence to every panel. `sort=True`
exists for a single standalone panel and should not be used in a grid.

**`kind='point'` or `kind='bar'`.** Dot-and-whisker when the estimates are
effects and the reader is judging whether each crosses the reference; bars when
they are standardised magnitudes and the reader is comparing lengths. Bars
imply a meaningful zero baseline — do not use them for a ratio centred on 1
without re-expressing it as a log.

---

## 4. Uncertainty: intervals, not asterisks

Nothing in `nature_panels` draws significance stars, and this is a deliberate
constraint rather than an omission.

A star encodes one thing — that a statistic crossed a threshold — and hides
the two things the reader needs: the size of the effect and its precision.
Readers reliably decode `***` as "three times as important as `*`", which it
is not. And a threshold on a p-value is unstable in exactly the designs
figures are usually built from: repeated measures on the same units,
clustered sampling, or many entities each contributing many rows. There the
naive p-value is inflated by pseudo-replication and can be arbitrarily small
while the effect is negligible.

**What to draw instead**, in order of preference:

1. **The interval, on the estimate.** `forest` and `grouped_bars` both take
   interval bounds. Colour then encodes whether the interval excludes the
   reference — the same information a 95% CI star carries, but it survives
   bootstrap and cluster-robust intervals unchanged.
2. **A cluster bootstrap** when observations are nested inside units:
   resample the *units*, recompute the statistic, take the 2.5th and 97.5th
   percentiles. An interval excluding zero is the honest analogue of
   "significant" here.
3. **A distribution-free effect size** — Cliff's δ, a rank-biserial
   correlation, a difference in medians — when the quantity is ordinal or the
   distributions are badly non-normal.

State in the caption which interval is drawn (SD, SE, CI, bootstrap CI), the
level, and `n`. `style.md` requires this; it is also the first thing a
statistical reviewer looks for.

---

## 5. Compositions

A stacked bar answers "what is this made of" well. It answers "how big is it"
badly and "how did the third component change" worse, because only the bottom
segment sits on a common baseline.

```python
from nature_panels import stacked_bars
totals = stacked_bars(ax, x, {"Renewable": r, "Storage": s, "Conventional": c},
                      colors=[COST[k] for k in ("Renewable", "Storage",
                                                "Conventional")],
                      spec=p, value_labels=lambda v: f"${v/1000:.1f}k")
```

**Draw the total as its own mark.** In a stack the total exists only as the top
edge, at a different height in every group, which is precisely the comparison
the eye does worst. A line-and-marker layer over the stack puts the total on a
common baseline without giving up the composition — and "the total barely
moved while the mix changed completely" becomes visible instead of merely
being true. This is `total=True`, and it is the default.

**White separation between segments.** `edgecolor='white', linewidth=0.3`.
Adjacent segments of similar lightness otherwise merge into one block.

**`signed=True` for quantities with a real zero.** Positive components stack
upward and negative ones downward, so zero stays a baseline rather than
becoming an arbitrary point inside a bar. The total line is then the *net*,
which is usually the panel's actual claim and which no individual segment
shows. Passing negative values without `signed=True` raises, because the
segments would overlap and the top edge would silently stop being the total.

**Component order is fixed and semantic.** Order components once — largest at
the bottom, or by a physical logic — and keep that order and those colours for
the whole paper (`style.md` §10). Re-sorting per panel destroys the reader's
ability to track a component across a figure.

**Value labels need headroom.** Autoscale fits the bars, not the text on top of
them. `value_labels=` adds the labels and the headroom together.

---

## 6. Grouped comparisons

```python
from nature_panels import grouped_bars
grouped_bars(ax, x, {"Baseline": a, "Treated": b}, ci=bounds, spec=p)
```

The dodge arithmetic is the part rewritten per figure and got slightly wrong:
bar width is `group_width / n_series`, and offsets must be **centred** on the
tick, or each group drifts right of its own label as series are added.

Keep to three or four series. Beyond that the bars get narrower than their own
error bars and the panel wants to be a small-multiple grid (§12) or a line
chart, if the x axis is ordered.

`ci` takes interval **bounds** in `(n_groups, n_series, 2)` and converts them,
for the same reason as §3.

---

## 7. Relationships: the fit and its band

```python
from nature_panels import fit_line
st = fit_line(ax, x, y, spec=p)      # -> slope, intercept, r2, p, n, se_slope
```

**The band stops where the data stops.** A ribbon continuing past the observed
range is a claim about a region with no observations in it, and it is the part
of the panel a reviewer reads first. `fit_line` draws across the observed range
by default; `extend=True` is available and should be justified in the caption.

**Say which band it is.** `fit_line` draws the confidence interval *on the
fitted line* — narrow at the centroid, flaring at the ends. That flare is
information; a constant-width ribbon is a different and wrong object, and a
prediction interval is a third one, several times wider. The caption must name
which is drawn.

**Rasterise the points, keep the fit vector.** Above `rasterize_above` points
(default 5,000) the scatter is rasterised so the PDF stays under the 50 MB
submission cap, while axes, text and the fitted line remain editable vector —
which is what the artwork guide actually requires.

**A high R² on a curved cloud is still a bad fit.** Look at the panel, not the
number. If the residuals bend, the panel needs a different model or a
transformed axis, and the honest R² belongs to that model.

---

## 8. Too many points: density panels

Past roughly 5,000 points a scatter stops being a scatter and becomes a
silhouette: the interior is saturated, and everything the panel could say about
where the mass lies is hidden under overplotting.

```python
from nature_panels import density_field
mesh, counts, extent = density_field(ax, x, y, spec=p, cmap="Blues", log=True)
cb = fig.colorbar(mesh, ax=ax); cb.set_label("Count")
```

**A density panel needs a colour bar.** Without one the reader can see there is
structure but cannot say whether the dark region holds 60% of the data or 99%.
This is the most common omission in this family.

**`log=True` for counts with a long tail.** Linear normalisation on
long-tailed counts gives one bright cell and a black field. `LogNorm` turns it
back into readable structure (`style.md` §13).

**`clip` acts on x and y, not on the colour scale.** One long tail otherwise
takes 80% of the panel and compresses the mass of the data into a corner. The
default drops the top 1% of each axis. Clipping data out of a panel is a
reportable choice: state it in the caption, and quote the *plotted* n.

**Fill the background with the colormap's zero colour.** Left white, a density
panel grows a pale halo along its own support boundary that reads as a
feature of the data. `fill_background=True` is the default.

Alternatives worth preferring in specific cases: `hexbin` when the reader
needs to count, a 2D histogram with visible bins when the bin width is
meaningful, and a plain rasterised scatter at `alpha=0.15` when the individual
points are the evidence.

---

## 9. State over time

A time series whose interpretation depends on a regime — day/night,
charging/discharging, peak/off-peak, treated/untreated, before/after an
intervention — needs the regime *drawn*. Describing it in the caption makes
the reader do the alignment by hand.

```python
from nature_panels import runs, state_bands
state_bands(ax, runs(is_parked, t), "#FDDBC7", label="Parked", zorder=1)
state_bands(ax, runs(is_shaded, t, min_length=3), "#aba197",
            label="Shaded", zorder=2)
ax.plot(t, y, color=SERIES, lw=1.2, zorder=4)
```

**Close the run that is still open at the end.** Converting a boolean column
into spans is a four-line loop that everyone writes and that drops the final
span, because the loop only emits on a falling edge and the series ends while
the state is still true. That last span is usually the interesting one.
`runs()` handles it, along with all-true, all-false and empty inputs.

**`min_length` filters sampling artefacts.** A state column derived from a
threshold flickers at the sample rate. Bands one sample wide are visual noise
that reads as structure.

**Keep the zorder ladder explicit**: bands 1–2, grid 3, data 4 and above.
Matplotlib will otherwise draw a 25%-alpha rectangle over the line the panel
is about.

**One legend entry per regime, not one per occurrence.** `state_bands` labels
only the first span. A regime occurring eleven times otherwise contributes
eleven identical legend entries, which is the difference between a usable
legend and an unusable one.

**Label the meaningful time unit**, not the raw index — day names across a
168-hour week, months across a year, band centres rather than boundaries. See
`style.md` §16. And run the series through `auto_unit` so the tick values land
in 0.1–999 (`style.md` §4): `Power (kW)` reads, `Power (W)` with `×10³` does
not.

---

## 10. Matrices

```python
from nature_panels import matrix_panel
mesh = matrix_panel(ax, np.corrcoef(X.T), labels=names, spec=p,
                    triangle="lower")
```

**Centre the colour scale; do not stretch it to the data.** A correlation
matrix normalised over its observed range puts the neutral colour at whatever
the mean correlation happens to be, so the same matrix changes its apparent
sign structure when a variable is added or dropped. `vcenter=0` pins it. Pass
`vcenter=None` only for a genuinely sequential quantity such as a confusion
count.

**Mask the redundant half of a symmetric matrix.** Both halves spend half the
panel restating the other half and make the diagonal harder to find.

**Print the numbers only when they fit.** `matrix_panel` measures the widest
label against the cell width and suppresses annotation when it will not fit,
rather than producing overlapping digits. When the numbers matter more than
the pattern, the honest answer is a table, not a smaller font.

Use a full box (`clean_axes(ax, box=True)`) or no spines at all for a matrix —
the two-spine default belongs to bar and line charts.

---

## 11. Flow panels (Sankey / alluvial)

Not implemented in `nature_panels`: matplotlib has no usable Sankey for real
data. Use plotly (`go.Sankey`) or R, and treat it as a production problem.

**Pin the node coordinates.** Plotly's automatic layout reorders nodes between
runs, so the figure changes shape every time the script is re-run and
co-authors review different pictures. Set `x` explicitly per stage and `y`
explicitly within each stage. This is the single most important thing to do to
a Sankey.

**Colour the links by the entity's group, not by the stage.** A link coloured
by its source stage cannot be traced across three stages; coloured by the
group it belongs to, the reader can follow a cohort end to end — which is the
only reason to draw more than two stages.

**Draw only the units that moved, and state the denominator.** A transition
diagram including everything that stayed put is dominated by wide
self-transition ribbons carrying no information. Filter to the movers and put
the total in the caption: "of 1,043 units, the 218 that changed class".

**Hairline white between links**, matching the stacked-bar rule in §5 — flows
of similar colour otherwise merge into one ribbon.

**Export SVG or PDF, never PNG**, and **draw the legend separately in
matplotlib** as patches, then place it at assembly. Plotly cannot produce a
house-style frameless legend at a landed type size, and this is exactly the
standalone-legend workflow of SKILL.md Step 5.

Readability ceiling is the same as for chords: about 10–15 nodes per stage and
three stages. Past that, aggregate or switch to a transition matrix (§10).

---

## 12. Small-multiple grids

```python
from nature_panels import ragged_grid, tidy_grid
axes, n_rows = ragged_grid(fig, n=17, n_cols=6)
tidy_grid(axes, n_cols=6, xlabel="Scenario", ylabel=r"Cost (USD capita$^{-1}$)")
```

**The bottom row is ragged, and that breaks the usual rule.** The standard
"only the outer ring carries labels" test is `row == n_rows - 1`. When the
last row is short, the bottom-most panel of several columns is *not* in the
last row, and that test blanks its tick labels, leaving whole columns with no
x axis. The correct test is `i + n_cols >= n`. `nature_style.share_outer_labels`
assumes a full rectangle; `tidy_grid` handles the ragged case.

**Hide unused slots** rather than leaving empty framed boxes — `ragged_grid`
does it.

**One shared legend and one shared axis label**, placed with `fig.supylabel`
or exported standalone (`export_legend`). Per-panel legends in a grid of
twelve repeat the same six entries twelve times.

**Every panel shares limits unless the point is that they differ.** Free axes
in a small-multiple grid make every panel look the same shape, which is the
opposite of what a grid is for. If one panel genuinely needs its own scale,
mark it — a stated range in the panel, or a break.

**Keep tick density down**: `MaxNLocator(nbins=4)`. Matplotlib's defaults are
tuned for one large axes and produce collisions at grid scale.

---

## 13. Panel audit

Run this before export, per panel. It is the §1 list turned into checks, plus
the recipe-specific ones.

- [ ] Spread drawn, or `n` stated in the panel or the caption
- [ ] Reference line present where one exists (zero, 1:1, baseline, break-even)
- [ ] Category order matches every other panel in the figure and the paper
- [ ] Interval type named in the caption (SD / SE / CI / bootstrap CI) with level
- [ ] No significance asterisks (§4)
- [ ] Colour bar present on any panel where colour carries a continuous value
- [ ] Units in the axis label; tick values in 0.1–999 (`auto_unit`)
- [ ] In-script text is data-derived only; callouts deferred to assembly
- [ ] Scatter above ~5,000 points rasterised or replaced by a density panel
- [ ] Any clipping, subsampling or filtering stated in the caption
- [ ] Violin: whiskers are Tukey, not extrema; groups below n ≈ 20 not violined
- [ ] Forest: intervals passed as bounds, estimates standardised or comparable
- [ ] Stack: total drawn as its own mark; negatives handled with `signed=True`
- [ ] Grid: ragged bottom row keeps its tick labels; unused slots hidden
