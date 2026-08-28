# Decision rules: gates, channels, tie-breaks

How to go from "intent ②, n = 40, 6 groups" to a specific chart.

## Table of contents

1. The gates (Gate 0 first, then A–F)
2. Encoding-channel ranking
3. Gate tables per intent
4. Tie-break heuristics
5. When one figure is really two
6. Figure-set planning for a whole paper

---

## 1. The gates

Answer these before shortlisting. Each eliminates candidates mechanically.
Gate 0 runs first and overrides the rest: get the scale wrong and no chart type can
recover the claim.

### Gate 0 — Scale and aggregation level

**The default is wrong.** Handed a dataframe and asked to plot it, both an AI
assistant and a tired researcher produce the most aggregated view the data permits:
the grand total, the pooled mean, the single global line. Papers almost never argue at
that level.

Decide three things, in this order:

| | Question | Wrong-by-default answer | Usually right |
|---|---|---|---|
| **Aggregation level** | What does one mark represent? | the whole dataset | one region / one scenario / one site |
| **Comparison unit** | Who is compared with whom? | nothing — one number | region vs region, scenario vs scenario, case vs its own baseline |
| **Granularity** | How finely is each axis resolved? | annual / global | hourly, per-site, per-subgroup |

**Match the scale to the verb of the claim sentence**

| Claim contains | Required scale |
|---|---|
| "across", "between", "varies", "heterogeneous", "some … while others" | disaggregated: facet, ridgeline, per-group violin, small multiples |
| "on average", "in total", "globally" | aggregated: one summary mark, with spread shown |
| "in region X", "for unit Y" | a single case, possibly with the ensemble de-emphasised behind it |
| "rises from A to B" | a decomposition (waterfall) or a paired change (dumbbell), not two separate totals |

**Failure signatures**

- One bar / one line / one number, but the claim was about variation.
- `groupby().sum()` at the top level with no facet, while the sentence says "across".
- The figure looks flat and unsurprising — opposing group trends have cancelled.
  (This is Simpson's paradox arriving as a boring figure rather than a wrong one.)
- A reviewer asks "does this hold everywhere?" and the figure cannot answer.
- 23 regional panels for a claim about the global total — over-disaggregation buries
  the point just as effectively.

**Escalation rule**: when unsure, drop exactly one aggregation level and look again.
Global total → per-region small multiples. Pooled distribution → per-group ridgeline.
Single mean line → per-scenario lines with the ensemble de-emphasised.

**De-escalation rule**: if the disaggregated figure has no visible structure — all
panels look alike — the heterogeneity claim is not supported, and the honest figure is
the aggregated one plus a statement that variation is small.

Record the decision before continuing:

```
one mark    = <entity>
comparison  = <unit A> vs <unit B>
granularity = <axis resolution>
```

### Gate A — Category count

| Count | Consequence |
|---|---|
| 2 | Dumbbell, paired plot, split violin, diverging bar all become available |
| 3–6 | Standard grouped/overlaid charts work; a legend is readable |
| 7–20 | Facet into small multiples, or emphasise one or two and let the rest recede |
| > 20 | Only heatmap, ridgeline, ranked dot plot, or map survive |

### Gate B — Sample size n

| n | Consequence |
|---|---|
| < 30 | **Show every point.** Beeswarm, strip, paired lines. Density estimates are not credible |
| 30–200 | Raincloud, violin + points, box + points |
| 200–10,000 | Violin, box, KDE, scatter with `alpha` |
| > 10,000 | Hexbin, 2D KDE, contours, ECDF. A plain scatter is the wrong chart, not a badly styled one |

### Gate C — Ordered or nominal?

Ordered (time, dose, latitude, severity, year) → the ordering must be visible:
sequential colour ramp, sorted axis, ridgeline, connected line.

Nominal (country, method, material) → qualitative palette, sorted **by value** rather
than alphabetically, unless a conventional order exists.

Sorting nominal categories alphabetically is a wasted encoding channel. Sort by the
quantity the claim is about.

### Gate D — Variable count shown at once

| Variables | Available approaches |
|---|---|
| 1 | Distribution charts |
| 2 | Scatter, line, bar, heatmap row |
| 3 | Bubble (area), colour-coded scatter, faceted 2-variable chart, dual-encoded map |
| 4 | Facet grid + colour, small multiples |
| > 4 | Parallel coordinates, SPLOM, dimensionality reduction, or **split into several figures** |

Three variables is where most figures break. Prefer faceting over piling on channels.

### Gate E — Is there a reference value?

If a zero, threshold, break-even, 1:1 line, target, or policy limit exists, the chart
type must be able to display it, and the figure must display it. This gate promotes:

- diverging bars over plain bars (when a zero exists)
- parity plots over generic scatter (when predicted vs observed)
- quadrant plots over generic scatter (when two thresholds exist)
- diverging colormaps over sequential (when a meaningful centre exists)

A chart with a natural reference value but no reference line is a missed argument.

### Gate F (extra) — Repeated measurements

If the experiment was run more than once, or the estimate has sampling error,
uncertainty **must** be shown: error bars, bands, CIs, or the raw replicate points.
Charts that cannot carry uncertainty (pie, treemap, streamgraph) are then disqualified
unless uncertainty genuinely does not apply.

---

## 2. Encoding-channel ranking

Cleveland–McGill, in decreasing order of how accurately humans read the encoded value:

1. **Position along a common scale** (aligned bar heights, points on a shared axis)
2. **Position along unaligned scales** (small multiples with independent axes)
3. **Length** (unaligned bar segments, e.g. middle segments of a stacked bar)
4. **Slope / angle**
5. **Area** (bubble size, treemap rectangles)
6. **Colour saturation / lightness**
7. **Colour hue** (nominal only — carries no magnitude)
8. **Volume** (never use)

Practical consequences:

- The quantity the claim is about goes on channel 1 or 2 whenever possible.
- Stacked bars put every segment except the bottom one on channel 3 — fine for
  composition, bad for comparing a middle segment across bars.
- Pie charts use channel 4; that is why they fail beyond a few slices.
- Bubble size must map to **area**, not radius: `s = k * value` in matplotlib
  (`s` is already in pt²), never `s = k * value**2`.
- Colour is excellent for nominal grouping and poor for precise magnitude. If the
  reader must extract numbers from a colormap, add contour lines or annotate values.

---

## 3. Gate tables per intent

### Intent ① Comparison

| Situation | Chart |
|---|---|
| ≤6 nominal categories, one measure | Bar (sorted) |
| Long labels or >8 categories | Horizontal bar / dot plot |
| Category × group, groups ≤4 | Grouped bar |
| Category × group, groups >4 | Small multiples |
| Total and parts both matter | Stacked bar |
| Only the mix matters | 100% stacked bar |
| Exactly two states per category | Dumbbell / slope graph |
| Signed values | Diverging bar |
| Decomposition of a change A→B | Waterfall |
| Many methods × many benchmarks | Heatmap matrix |
| Estimates with CIs across studies | Forest plot |

### Intent ② Distribution

| Situation | Chart |
|---|---|
| n < 30, few groups | Beeswarm / strip with mean line |
| n 30–200, few groups | Raincloud |
| Many groups, compact space | Box plot (or violin if multimodality matters) |
| Two conditions, same axis | Split violin |
| Many **ordered** groups | Ridgeline |
| "What fraction exceeds X?" | ECDF |
| Distribution attached to a scatter or map | Marginal density |
| Checking a distributional assumption | Q–Q plot |

The n boundaries above are indicative, not gates. They mark roughly where a
fitted density stops being believable and the raw points start carrying more
information — the exact crossover depends on how much structure the
distribution has. Nothing in this skill applies an n cutoff automatically;
when you pick one, record the number and why.

### Intent ③ Composition

| Situation | Chart |
|---|---|
| ≤5 parts, one moment, lay audience | Pie / donut |
| Parts over continuous time | Stacked area |
| Hierarchy, many leaves | Treemap |
| Hierarchy ≤3 levels, emphasis on nesting | Sunburst |
| Two categorical variables jointly | Mosaic |
| Recategorisation across variables | Parallel sets |

### Intent ④ Relationship

| Situation | Chart |
|---|---|
| n < 10k, two continuous | Scatter (+ LOWESS if a trend is claimed) |
| n > 10k | Hexbin / 2D KDE |
| Predicted vs observed | Parity plot with `y=x`, R², RMSE |
| Method agreement | Bland–Altman |
| Two thresholds create named classes | Quadrant plot |
| Many variables, pairwise | Correlation heatmap |
| Multi-objective solutions | Pareto frontier / parallel coordinates |
| Third variable, moderate range | Bubble (area) |

### Intent ⑤ Trend

| Situation | Chart |
|---|---|
| One or few series, continuous time | Line |
| Replicates or model ensemble | Line + band (state SD/SE/CI) |
| Discrete state changes | Step |
| Mix over time | Stacked area |
| Diurnal × seasonal structure | Hour × day heatmap |
| Effect around an intervention | Event-study plot |
| Two incomparable units | **Two panels**, not a dual axis |

### Intent ⑥ Spatial

| Situation | Chart |
|---|---|
| Discrete sites | Point map (colour = value, white edges) |
| Administrative aggregates | Choropleth (equal-area projection) |
| Magnitude where area would mislead | Proportional symbol map |
| Two variables at once | Dual-encoded points, or bivariate choropleth |
| Continuous field | Raster map |
| Origin–destination | Flow map / chord |
| Several variables | Map small multiples |
| Pattern along latitude/longitude | Map + transect profiles |

### Intent ⑦ Flow and network

| Situation | Chart |
|---|---|
| Conserved flow through ≤4 stages | Sankey |
| Entities changing category across scenarios | Sankey / alluvial (nodes ordered consistently) |
| Bidirectional matrix, ≤15 nodes | Chord |
| Topology and communities | Network graph (filtered) |
| Causal assumptions | DAG |
| Method steps | Flowchart |

### Intent ⑧ Uncertainty

| Situation | Chart |
|---|---|
| Regression results | Coefficient plot with CIs |
| Multiple studies/subgroups | Forest plot |
| One-at-a-time sensitivity | Tornado |
| Global sensitivity | Sobol variance bars |
| Propagated simulation uncertainty | Distribution + quantile bands |
| Classifier, balanced | ROC |
| Classifier, imbalanced | Precision–recall |
| Component contributions | Ablation bars |

---

## 4. Tie-break heuristics

When two candidates survive all gates:

1. **Which one shows the raw data?** Prefer it. Reviewers trust figures that reveal n
   and spread.
2. **Which one needs less explanation in the caption?** Prefer it.
3. **Which one is conventional in the target field?** Familiarity buys comprehension
   speed; deviate only for a real gain.
4. **Which one still works in greyscale?** Prefer it.
5. **Which one still works at 88 mm wide?** Many designs die at single-column width.
   Test early.
6. **Which one degrades more gracefully if the data changes?** Figures get regenerated
   after revisions; a design that breaks when a category is added is a liability.

---

## 5. When one figure is really two

Split when any of these hold:

- The claim sentence contains "and" joining two different verbs
  ("costs rise **and** the mix shifts").
- The two quantities have incomparable units and a dual axis is being considered.
- More than ~4 series overlap and a legend is needed to disentangle them.
- One part of the figure needs a log scale and another needs linear.
- The caption is heading past ~5 sentences.

Splitting is cheap. Panels `a` and `b` of one figure cost nothing and read far better
than one overloaded axes.

---

## 6. Figure-set planning for a whole paper

A typical high-impact paper carries 4–6 main figures with an implicit narrative:

| Position | Job | Typical intents |
|---|---|---|
| Fig 1 | Establish the phenomenon and its scale | ⑥ spatial + ② distribution |
| Fig 2 | Define the classification or key metric | ④ relationship (quadrants) + ⑥ spatial |
| Fig 3 | Show what changes under stress or intervention | ⑦ flow + ② distribution + ⑧ inference |
| Fig 4 | Show the proposed remedy and who it helps | ① comparison + ⑦ flow |
| Fig 5 | Mechanism, cost, or policy implication | ① comparison + ⑧ uncertainty |

Rules for the set as a whole:

- **One claim per figure**, and the claims should form an argument in order.
- **Semantic colours are shared across the whole set** — a category introduced in
  Fig 2 keeps its colour in Fig 3, Fig 4, and the supplement.
- **Escalating complexity**: the first figure should be the easiest to read.
- Anything that supports rather than advances the argument belongs in the supplement.
- Write all captions together, in order, and read them alone end to end. If that
  sequence does not tell the paper's story, the figure set is wrong regardless of how
  good any single figure looks.
