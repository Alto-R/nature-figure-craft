# Anti-patterns

Symptom → cause → prescription. Severity: **CRITICAL** (misleads the reader),
**MAJOR** (obscures the claim), **MINOR** (cosmetic noise).

## Table of contents

1. Wrong chart for the claim
2. Charts that mislead
3. Charts that hide
4. Overload
5. Style noise that is really a type problem
6. Caption failures
7. Quick audit

---

## 1. Wrong chart for the claim

| Symptom | Cause | Prescription | Severity |
|---|---|---|---|
| Bar chart with a time axis | Categorical chart used for a continuous ordered variable | Line or step chart | MAJOR |
| Pie chart with 12 slices | Proportion chart used for magnitude comparison | Sorted horizontal bar | MAJOR |
| Several pie charts side by side to compare | Angle comparison across separate origins | Stacked bars, or a slope/dumbbell of the shares | MAJOR |
| Line chart connecting nominal categories | Implies an ordering that does not exist | Bar or dot plot | MAJOR |
| Radar chart with incomparable axes | Enclosed area is meaningless when units differ or axis order is arbitrary | Small multiples of bars, or a normalised heatmap row | MAJOR |
| Scatter used for two categorical variables | Wrong data type | Mosaic plot or heatmap | MAJOR |
| Stacked bars used to compare a middle segment | Middle segments have unaligned baselines (perceptual channel 3) | Small multiples, one panel per component | MAJOR |
| Grouped bars with 8 groups | Beyond legend-tracking capacity | Small multiples or heatmap | MAJOR |

## 2. Charts that mislead

| Symptom | Cause | Prescription | Severity |
|---|---|---|---|
| **Dual y-axis showing "strong correlation"** | Each axis can be rescaled arbitrarily; any two series can be made to look coupled | Two stacked panels sharing x, or standardise both to z-scores on one axis | **CRITICAL** |
| Bar chart y-axis starting at 59% | Truncated baseline exaggerates differences | Bars start at zero. If differences are genuinely small, use a dot plot with a truncated axis and mark it | **CRITICAL** |
| 3D bar / 3D pie | Perspective distorts magnitudes; occlusion hides data | 2D always, unless the data are genuinely 3D | **CRITICAL** |
| Bubble size scaled by radius | Perceived quantity is area, so the encoding is squared | `s` in matplotlib is already area; map value → area linearly | **CRITICAL** |
| Choropleth where Siberia dominates | Area ≠ importance | Proportional symbols, cartogram, or hex tile map | MAJOR |
| Colormap clipped without notice | Extreme values silently collapsed into the end colour | `extend='both'` on the colorbar; state the percentile limits | MAJOR |
| Rainbow / `jet` colormap | Perceptually non-uniform; invents boundaries; fails for colour-blind readers | `viridis`, `cividis`, or `RdBu_r` | MAJOR |
| Diverging colormap not centred on the meaningful zero | The white midpoint lands at an arbitrary value | `TwoSlopeNorm(vcenter=0)` | MAJOR |
| Linear norm on long-tailed count data | 99% of cells look identical | `LogNorm` | MAJOR |
| Regression line extrapolated past the data | Implies support that does not exist | Clip the line to the data range | MAJOR |
| Trend line on non-monotone data | The smoother hides structure | Show the scatter; use a flexible smoother or none | MAJOR |
| Cherry-picked axis range hiding outliers | Data removed without disclosure | Show all data, or state the exclusion rule in the caption | **CRITICAL** |
| Independent y-limits in small multiples, undisclosed | Reader compares heights that are not comparable | State it in the caption, or share limits | MAJOR |

## 3. Charts that hide

| Symptom | Cause | Prescription | Severity |
|---|---|---|---|
| **Bar of means with error bars only** | Shape, n, and outliers are invisible; bimodality is undetectable | Raincloud, violin + points, or beeswarm | MAJOR |
| Box plot on a bimodal distribution | The box shows only quartiles | Violin or raincloud | MAJOR |
| Error bars with no definition | SD, SE, and CI differ by large factors | Caption states which, and n | **CRITICAL** |
| No uncertainty shown despite replicates | Reader cannot assess reliability | Error bars, bands, or raw replicate points | MAJOR |
| Histogram with default bins | Bin width drives the apparent shape | Try several widths; consider ECDF, which has no bin parameter | MINOR |
| KDE on bounded data | Density leaks past a physical bound (e.g. below zero) | Reflect at the boundary, or use a histogram/ECDF | MINOR |
| Aggregated means hiding Simpson's paradox | Group structure not shown | Facet by group, or overlay group-level lines | **CRITICAL** |
| n not reported anywhere | Reader cannot weight the evidence | Report n per group in the caption or on the axis | MAJOR |
| **One global total for a claim about variation** | The default most-aggregated view was accepted by inertia — the classic AI-generated-figure failure | Drop one aggregation level: per-region small multiples, per-group ridgeline, per-scenario lines | MAJOR |
| Figure looks flat and unsurprising | Opposing subgroup trends cancelled under aggregation | Disaggregate and check whether the flatness survives | MAJOR |
| 23 regional panels for a claim about the global total | Over-disaggregation; the point is buried | Aggregate up, or move the panels to the supplement | MAJOR |
| Hourly resolution for an annual claim (or vice versa) | Granularity mismatched to the sentence | Resample to the scale the claim is made at | MINOR |

## 4. Overload

| Symptom | Cause | Prescription | Severity |
|---|---|---|---|
| 50,000 points as an opaque blob | Over-plotting; wrong chart type for n | Hexbin, 2D KDE, contours; or `alpha=0.15` + `rasterized=True` | MAJOR |
| Seven equally saturated series | Beyond visual tracking capacity | Emphasise the one or two the claim is about and let the rest recede; or facet | MAJOR |
| Four encoding channels on one panel | Colour + size + shape + hatch all varying | Move one channel to a facet | MAJOR |
| Legend with 40 entries | The categories are not individually readable anyway | Group into tiers, or label directly on the marks | MAJOR |
| One figure making three claims | The figure has no single message | Split into panels or separate figures | MAJOR |
| Caption 300 words long | The figure is doing too much | Split | MAJOR |
| Every subplot repeats the axis label | Redundant ink | Outer ring only, plus `supylabel` | MINOR |

## 5. Style noise that is really a type problem

These look cosmetic but are usually symptoms of a wrong choice.

| Symptom | What it really means |
|---|---|
| Tick labels rotated 90° to fit | Too many categories → horizontal bar or facet |
| Font shrunk to 4 pt to fit the legend | Too many series → tier or facet |
| Heavy grid needed to read values | Values matter → annotate them directly, or use a table |
| Text annotations covering the data | The chart is too dense → split |
| A second legend explaining the first | Two encodings are competing → move one to a facet |
| Log axis added late "so everything fits" | Two populations differ by orders of magnitude → they may deserve separate panels |

## 6. Caption failures

| Symptom | Prescription | Severity |
|---|---|---|
| "Figure 5: Results on BIRD." | First sentence states the **finding**: "Our method outperforms all baselines on BIRD across model sizes, with the largest gains on complex multi-table queries." | MAJOR |
| Abbreviations used in the figure but undefined | Define every one in the caption or legend | MAJOR |
| Statistical test unnamed | Name the test, the n, and the correction for multiple comparisons | **CRITICAL** |
| Caption repeats the axis labels | Say what the figure *shows*, not what is written on it | MINOR |
| Panels not all described | Every panel letter gets a sentence | MAJOR |
| Error definition absent | State SD / SE / CI and n | **CRITICAL** |

## 7. Quick audit

Twelve questions. Any "no" is a finding.

1. Can you state the figure's claim in one sentence?
2. Is the figure at the **scale** the claim is made at — neither aggregated past it nor
   scattered below it?
3. Does the chart type express that exact claim?
4. Is the claim's quantity on a high-accuracy channel (position or length)?
5. Is the raw distribution visible, or at least n reported?
6. Is uncertainty shown and defined?
7. Are the axes honest (zero where it matters, breaks marked)?
8. Is there a reference line where a "good direction" exists?
9. Is the figure readable without any explanatory text inside the plot area?
10. Does it survive greyscale printing and colour-vision deficiency?
11. Does it survive being printed 88 mm wide?
12. Does the caption's first sentence state the finding?
