# Multi-panel composition templates

Ten layouts that recur in high-impact figures. They are not chart types — they
are ways of *arranging* chart types so that one figure carries a complete
argument.

Each template lists: what it answers, the panel anatomy, when it fails, and the
scaffolding.

> **Limits.** This is a reference set of arrangements known to have worked, not
> a taxonomy and not a checklist to satisfy. Expect a different field or a
> different argument to need layouts that are not here, and expect some of these
> to be wrong for your figure.

## 0. Which of these need coordinates

Three of the ten are geographic and are dead weight for a paper without
lat/lon. Skip straight past them.

| | Template | Needs coordinates |
|---|---|---|
| 1 | Map + marginal profiles | **yes** |
| 2 | Distribution ‖ map, paired rows | **yes** (the map half) |
| 3 | Main plot + zoom inset + marginals | no |
| 4 | Semantic quadrants | no |
| 5 | Sankey for state migration | no |
| 6 | Ridgeline + mirrored bars | no |
| 7 | Small multiples | no |
| 8 | Ablation ladder + per-case spread | no |
| 9 | Metric matrix small multiples | no |
| 10 | Trajectory + endpoint | no |

Template 2 degrades cleanly: replace the map column with any second view of the
same component — a small time series, a per-group bar, a confusion sub-matrix.
The template is "one row per component, two complementary views", and geography
is only one way to fill the right-hand column.

## Table of contents

1. Map + marginal profiles
2. Distribution ‖ map, paired rows
3. Main plot + zoom inset + marginals
4. Semantic quadrants
5. Sankey for state migration
6. Ridgeline + mirrored bars
7. Small multiples
8. Ablation ladder + per-case spread
9. Metric matrix small multiples
10. Trajectory + endpoint
11. Choosing between them
12. The one thing they share

---

## 1. Map + marginal profiles

**Answers**: where is it, and how is it distributed along latitude and longitude?

**Anatomy**
```
┌──────────────────────────┬────┐
│                          │ d  │  d = latitude density (rotated KDE)
│      a  point map        │    │
│                          │    │
├──────────────────────────┴────┤
│  c  longitude density         │
└───────────────────────────────┘
```

Panel `a` is the map; `c` and `d` are marginal density curves sharing the map's x and
y axes. The eye reads the map for pattern, then the margins for "the mass sits in the
tropics" — a claim the map alone cannot make quantitatively.

**Fails when**: points are globally uniform (margins add nothing), or when the metric
is a regional aggregate rather than a point value.

```python
gs = fig.add_gridspec(2, 2, width_ratios=[6, 1], height_ratios=[6, 1],
                      wspace=0.03, hspace=0.03)
ax_map = fig.add_subplot(gs[0, 0], projection=ccrs.Robinson())
ax_lat = fig.add_subplot(gs[0, 1])   # sharey conceptually
ax_lon = fig.add_subplot(gs[1, 0])   # sharex conceptually
```

## 2. Distribution ‖ map, paired rows

**Answers**: for each component of a decomposition — how much, and *where* (or, in
the non-geographic version, and *under what condition*)?

**Anatomy**: N rows, one per component. Each row = a raincloud / violin on the left
and a second, complementary view on the right — an inset map, a small time series, a
per-group bar, whatever answers the "and where does it come from" question.

```
┌───────────────────────────┬────────┐
│  raincloud: component A   │ 2nd    │
├───────────────────────────┼────────┤
│  raincloud: component B   │ view   │
├───────────────────────────┼────────┤
│  raincloud: component C   │        │
└───────────────────────────┴────────┘
```

The row colour is the component's semantic colour, reused in every other figure.

**Fails when**: components are not comparable in units, or when N > 6 (rows become
too short to read).

## 3. Main plot + zoom inset + marginals

**Answers**: what is the global structure, and what is happening in the dense corner?

**Anatomy**: full-range scatter with an axes-inset showing the crowded sub-range,
plus marginal KDE curves on top and right. Optionally `mark_inset` to draw the
connector lines.

```python
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

axin = ax.inset_axes([0.05, 0.45, 0.5, 0.5])
axin.set_xlim(0, 0.5); axin.set_ylim(0, 0.8)
# replot the same data into axin
mark_inset(ax, axin, loc1=2, loc2=4, fc='none', ec='#888', lw=0.5)
```

**Fails when**: the data is not actually concentrated — then the inset is decoration.
Check first: if 90% of points fall in <20% of the axis range, an inset earns its place.

## 4. Semantic quadrants

**Answers**: which named category does each observation fall into, and how does the
population split?

This is the highest-leverage template in the set. It converts a continuous 2D scatter
into a small set of **named, memorable classes**, and those class colours then
propagate to every other panel in the paper — bar charts, maps, Sankey diagrams.

**Anatomy**
- x and y = two continuous decision variables (e.g. cost vs willingness to pay)
- one **diagonal** dividing line with real meaning (break-even, `y = x`)
- one or two **threshold** lines (medians, policy limits)
- resulting regions filled with a low-alpha **ordered** colour ramp
  (dark blue = best → light blue → light red → dark red = worst)
- points drawn on top with white edges
- optional marginal histograms above and right — that is where a reader checks
  whether a threshold sits in a valley or in the middle of a mode
- the legend is a **thumbnail of the partition itself**, exported standalone

```python
from nature_quadrant import threshold, regions, region_background, divider

t = threshold(df.cost, 'median')                  # value + a caption string
part = regions([...], default='Unviable')         # classify(x, y) -> class name
region_background(ax, part, xlim, ylim)           # the classifier, on a grid
divider(ax, x=t.value, diagonal=True, spec=p)     # grey median, accent break-even
```

**Layout ratios**: main panel square or close to it; marginals 15–25% of its
height and width; inset ≤ 45% of the panel, placed near the region it magnifies
so the connectors stay short.

**Rules** — full method in [quadrant.md](quadrant.md), of which this template is
the layout half:
- Name the classes for the **data condition**, in words, never for a screen
  position — axes get inverted at assembly and "top right" does not survive it.
- The dividing lines must be *derived*, not eyeballed: break-even from physics,
  thresholds from a stated statistic (global median) — and stated in the caption.
  Recount the classes under a defensible alternative line before publishing; if
  the headline flips, the classification is not a finding.
- Reuse the class colours everywhere afterwards. That is the whole point.

**Fails when**: the split has no physical meaning, or when class counts are so uneven
that four of six regions are empty.

## 5. Sankey for state migration

**Answers**: as conditions change, which entities move from good states to bad ones?

Usually thought of as an energy/material flow diagram, but its most powerful academic
use is **categorical migration across scenarios or time**:

```
Entities ──► Best case ──► Baseline ──► Stressed case
```

The stages can be scenarios, time points, model versions, or successive filtering
steps. Node colours = the semantic classes from template 4. Ribbon width = number of
entities. Crossing ribbons are exactly the story: who changed class, and in which
direction.

**Rules**
- 3–4 stages maximum; more becomes unreadable.
- Order nodes consistently at every stage (best at top, worst at bottom) so vertical
  position itself encodes rank and crossings become visually meaningful.
- Ribbon alpha ~0.6–0.75 so crossings stay legible.
- Label the stage axis at the bottom in bold.

**Fails when**: fewer than ~5% of entities actually change state (a table is better),
or when the categories are not mutually exclusive.

Tools: `plotly.graph_objects.Sankey` (export SVG then restyle in Illustrator), or
`matplotlib` + manual Bezier ribbons for full control.

## 6. Ridgeline + mirrored bars

**Answers**: how does a distribution shift across an ordered set of groups, and how
big is each group?

**Anatomy**: shared y-axis of groups (regions, years, parameter values).
Left column = overlapping KDE ridges, two scenarios in two colours.
Right column = diverging horizontal bars (counts, positive/negative split).

```
        ridge (distribution shape)      bars (magnitude)
grp 1 ▁▂▄█▆▂▁                          ████████▏
grp 2 ▁▃█▅▂                            █████▏
grp 3 ▂█▄▁                             ██▏
```

The groups must be *ordered* by something — a region along a gradient, a year, a
dose, a model size, a hyperparameter. Nominal groups make a ridgeline meaningless.

Sort groups by a meaningful statistic (median shift), not alphabetically.

**Fails when**: fewer than ~6 groups (use grouped violins), or when distributions are
so similar that the ridges overlap into mush.

## 7. Small multiples

**Answers**: is the headline result homogeneous, or does it vary by unit?

**Anatomy**: an N-column grid of identical miniature charts, one per region / site /
condition; one shared legend at the bottom; one shared axis label via `supylabel`.

**Rules**
- **Independent y-limits are honest** when magnitudes differ by orders of magnitude —
  but then the reader compares *shape*, not height, and the caption must say so.
  Shared limits when comparing magnitude is the point.
- Annotate each panel with its total so magnitude is still recoverable
  (`f'${total/1000:.1f}k'` above each bar).
- x tick labels only on the bottom-most used panel of each column:

```python
if idx + n_cols >= n:
    ax.set_xticklabels(labels, rotation=45, ha='right')
else:
    ax.set_xticklabels([])
for k in range(n, len(axes)):
    axes[k].set_visible(False)      # hide empty grid slots
```

- Overlay a single black trend line on stacked bars to give a total that the stacking
  itself does not make readable.

**Fails when**: N > ~30 (use a heatmap), or when panels are so small that ticks
collapse.

## 8. Ablation ladder + per-case spread

**Answers**: which component actually carries the result, and does the aggregate
number hide cases where it does not?

**Anatomy**: left panel = the ladder, one row per configuration (full system, then
each component removed), sorted by effect size, with the full-system value as a
reference line running through all rows. Right panel = the per-case distribution
for the two or three configurations that matter, on the same y scale.

```
┌─────────────────────────────┬──────────────┐
│ full          ●─────────────│ ┊  raincloud │
│ − component A ●────────     │ ┊  full      │
│ − component B ●──────       │ ┊  vs        │
│ − component C ●────         │ ┊  − A       │
└─────────────────────────────┴──────────────┘
        ↑ reference line = full system
```

**Rules**
- **The ladder is a dot plot, not a bar chart.** The quantity is a *difference from
  the full system*, so a bar anchored at zero encodes the wrong baseline and makes
  a 2% drop look like a full column.
- Sort by effect, not by the order the components appear in the method section.
- The right panel exists because a mean ablation effect of "−3 points" is
  compatible with "−3 everywhere" and with "0 on 90% of cases and −30 on the rest",
  and those are different papers. If the spread is narrow, say so and drop the panel.
- If components interact, one-at-a-time removal is not a decomposition. Either
  report the combinations or state the assumption.

**Fails when**: more than ~8 configurations (becomes a table), or when removing a
component makes the system undefined rather than worse.

## 9. Metric matrix small multiples

**Answers**: does the ranking hold across metrics that have no common unit?

**Anatomy**: a row of small panels, one per metric. Shared categorical x (the
methods / models / conditions, in one fixed order everywhere), independent y per
panel because the units do not compare. One shared legend.

```
┌────────┐┌────────┐┌────────┐┌────────┐
│metric 1││metric 2││metric 3││metric 4│
│ ▁▄█▆   ││ █▆▄▁   ││ ▄█▁▆   ││ ▆▁█▄   │
└────────┘└────────┘└────────┘└────────┘
   same category order in every panel
```

**Rules**
- **This is the honest replacement for a radar chart.** A radar encloses an area
  whose size depends on the arbitrary order of the axes and on how each was
  normalised; the number a reader takes away is an artefact. Small multiples give
  up the single-glance shape and keep the values.
- **Fix the category order once**, by the metric the paper leads with, and keep it
  in every panel. Re-sorting each panel by its own metric destroys the comparison
  the figure exists to make.
- Mark the direction of good — "higher is better" as an arrow on the y axis, or by
  flipping the metrics that are inverted so that up is always better. Do it once,
  in the axis, not in prose per panel.
- Independent y limits mean the reader compares *rank and gap*, not height across
  panels. Say so in the caption.

**Fails when**: more than ~6 metrics (goes to a heatmap with annotated cells), or
when the metrics are so correlated that every panel shows the same ordering — then
one panel and a sentence is the figure.

## 10. Trajectory + endpoint

**Answers**: does it converge, and where does it land?

**Anatomy**: left panel = many runs over an iteration / epoch / time axis, drawn as
a median line with an inter-quantile band, one band per condition. Right panel,
sharing the y axis = the distribution of final values, as a violin or beeswarm.

```
┌────────────────────────────┬─────┐
│  ╱‾‾‾‾‾‾‾‾‾‾‾‾ condition A │  ▐█▌│
│ ╱   ╱‾‾‾‾‾‾‾‾  condition B │  ▐█▌│
│╱   ╱                       │     │
└────────────────────────────┴─────┘
   shared y axis ──────────────────┘
```

**Rules**
- **Never plot a single run.** A trajectory from one seed is an anecdote; the band
  is the result. State what the band is (quantiles across seeds, SD across folds)
  and how many runs, in the caption.
- The endpoint panel exists because the curves overlap exactly where it matters —
  at the right-hand edge, compressed into a few pixels. It un-compresses the one
  comparison the reader came for.
- Shared y axis, no gap between the panels, no repeated tick labels on the right.
- Log the x axis when the interesting behaviour is early; say so.

**Fails when**: the runs are deterministic (there is no band, so plot the curves),
or when the final values are so separated that the endpoint panel restates the
obvious.

---

## 11. Choosing between them

| The figure must show | Template |
|---|---|
| Spatial pattern + how it concentrates | 1 — map + marginals |
| A decomposition, each part's size and location | 2 — distribution ‖ map |
| A relationship whose interesting part is a dense corner | 3 — zoom inset |
| A classification derived from two continuous variables | 4 — semantic quadrants |
| Movement between categories across scenarios | 5 — Sankey |
| Distribution shift across many ordered groups | 6 — ridgeline + bars |
| Heterogeneity across many units | 7 — small multiples |
| Which component carries the result | 8 — ablation ladder |
| A ranking that must hold across incomparable metrics | 9 — metric matrix |
| Convergence behaviour and final performance | 10 — trajectory + endpoint |

Templates compose. A main figure is often 4 + 5 (define classes, then show migration),
1 + 7 (global map, then per-unit detail), or 10 + 8 (converges, and here is why).

## 12. The one thing they share

Every template above contains **a reference structure that tells the reader which
direction is good**: a break-even diagonal, a zero line, a median cross, an ordered
colour ramp, a consistent node ordering, a full-system baseline, a fixed category
order held across panels.

A panel without one is a picture of data. A panel with one is an argument.
