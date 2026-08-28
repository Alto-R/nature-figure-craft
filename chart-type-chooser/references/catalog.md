# Chart catalog: nine intents, ~70 types

Each entry: **what it can express** → **when not to use it**.

## Table of contents

1. Comparison
2. Distribution
3. Composition
4. Relationship
5. Trend and time
6. Spatial
7. Flow and network
8. Uncertainty and inference
9. Concept and schematic

---

## 1. Comparison — "A is larger than B"

| Chart | Can express | Do not use when |
|---|---|---|
| **Bar chart** | Magnitude across a few nominal categories | The x variable is continuous or time |
| **Grouped bar** | Category × group (method × benchmark) | Groups > 4; use small multiples |
| **Stacked bar** | Total and composition simultaneously | Comparing non-bottom segments (their baselines are unaligned) |
| **100% stacked bar** | Composition ratio only, totals irrelevant | The total itself matters |
| **Horizontal bar** | Long category names; ranked lists | Fewer than 4 categories (wastes width) |
| **Lollipop** | Many sparse categories, less ink than bars | Precise value reading is needed |
| **Dot plot (Cleveland)** | Ranked comparison, very high data-ink ratio | Values span orders of magnitude |
| **Dumbbell plot** | Change between exactly two states, per category, with direction | More than 2 states |
| **Slope graph** | Rank and value change between 2–3 time points | Many time points; many crossing lines |
| **Diverging bar** | Positive/negative split; two mirrored groups | Only positive values exist |
| **Population pyramid** | Two groups' symmetric distribution along an ordered axis | Groups are not naturally paired |
| **Radar / spider** | Multi-dimensional profile (≤8 axes, ≤3 series) | Axes have incomparable units, or axis order is arbitrary (the enclosed area is then meaningless) |
| **Heatmap matrix** | Large category × category comparison | Precise values needed and cells unannotated |
| **Bullet chart** | Actual vs target vs qualitative bands | More than one measure per row |
| **Waterfall** | Decomposition of the change from A to B (cost build-up, emission attribution) | More than ~8 components |
| **Forest plot** | Effect sizes with CIs across studies or subgroups | No uncertainty estimates available |
| **Pareto chart** | Ranked contributions plus cumulative share | Categories are not comparable in kind |

## 2. Distribution — "the values are spread like this"

| Chart | Can express | Do not use when |
|---|---|---|
| **Histogram** | Shape of one variable's distribution | n < ~50; bin choice then dominates the picture |
| **KDE curve** | Smooth density; several groups overlaid | n small, or the variable is bounded (KDE leaks past the bound) |
| **Box plot** | Median, IQR, whiskers, outliers; compact, many groups | The distribution is multimodal (a box hides it) |
| **Violin** | Full shape plus summary; split violins compare two conditions on one axis | n < ~30 per group |
| **Raincloud** | Half-violin + box + raw points — shape, summary, and every observation at once | Space is extremely tight |
| **Ridgeline (joyplot)** | How a distribution shifts across many *ordered* groups | Groups are nominal and unordered |
| **Beeswarm / strip / jitter** | Every individual observation, n < ~200 | n large (turns into a blob) |
| **ECDF** | Cumulative proportion; answers "what fraction exceeds X" exactly, with no binning assumption | The audience is unfamiliar and shape matters more than quantiles |
| **Q–Q plot** | Whether data follow an assumed distribution | Purely descriptive contexts |
| **Marginal density** | The distribution along an axis of a scatter or map | The marginal is uniform (adds nothing) |
| **Fan chart** | Widening uncertainty of a distribution over time | Uncertainty is constant |
| **Rug plot** | Individual values as ticks under another chart | n large |
| **Bagplot** | Bivariate analogue of a box plot | Audience unfamiliar |

**Rule**: a bar of means with error bars is not a distribution chart. If the claim is
about spread, use one of the above.

## 3. Composition — "it is made of these parts"

| Chart | Can express | Do not use when |
|---|---|---|
| **Pie / donut** | Proportions at one point in time, ≤5 slices | Comparing several pies; more than 5 slices; small differences |
| **Stacked area** | Composition evolving over a continuous axis | More than ~6 series, or series cross frequently |
| **Streamgraph** | Composition and total both changing; aesthetic emphasis | Precise reading is required (no common baseline) |
| **Treemap** | Hierarchical composition with size; hundreds of leaves on one screen | Comparing similar-sized rectangles precisely |
| **Sunburst** | Hierarchical composition, ≤3 levels | Deeper hierarchies (outer rings become unreadable) |
| **Icicle plot** | Hierarchy with readable labels | Very wide hierarchies |
| **Mosaic plot** | Joint distribution of two categorical variables with proportional areas | Many categories |
| **Parallel sets / alluvial** | How composition regroups across several categorical variables | More than ~4 variables |
| **Waffle chart** | Part-of-whole for a lay audience; counts of discrete units | Precise percentages matter |

## 4. Relationship — "these two things move together"

| Chart | Can express | Do not use when |
|---|---|---|
| **Scatter** | Association between two continuous variables | n > ~10,000 (over-plotting) |
| **Bubble chart** | Scatter plus a third variable as **area** | The third variable spans orders of magnitude |
| **Scatter + LOWESS / regression** | Trend and its confidence band inside noise | The relationship is not monotone and the smoother hides it |
| **Parity plot (1:1)** | Predicted vs observed; must carry the `y = x` line plus R² and RMSE | Only one of the two is available |
| **Bland–Altman** | Agreement between two measurement methods (difference vs mean) | The methods measure different constructs |
| **Correlation matrix heatmap** | All pairwise correlations among many variables | Causal claims are intended |
| **Hexbin / 2D KDE / contour** | Density of a relationship at large n | n small (cells become noise) |
| **Parallel coordinates** | High-dimensional solutions, multi-objective trade-offs | More than ~10 axes or hundreds of lines |
| **Scatterplot matrix (SPLOM)** | Exploratory view of all pairwise relations | Main text (too dense) |
| **Bivariate choropleth** | Two variables jointly encoded in space, via a 3×3 colour matrix | The audience cannot be given a legend key |
| **Quadrant / region plot** | Two continuous variables converted into named categories by meaningful dividing lines — 2×2, or more regions once a diagonal or a curved boundary is added | The dividing lines have no physical or statistical justification; the claim is about the *relation* rather than the classes; the classes are never reused elsewhere in the paper |
| **Pareto frontier** | The non-dominated set in multi-objective optimisation | Objectives are not genuinely conflicting |
| **Efficiency–effectiveness scatter** | Trade-off between cost/time and performance; "Ours" should sit toward the good corner | One axis has no variance |
| **Connected scatter** | Two variables' joint path over time | Time is not the ordering variable |

## 5. Trend and time — "it changes like this"

| Chart | Can express | Do not use when |
|---|---|---|
| **Line chart** | Trend along a continuous ordered axis | Categories are nominal |
| **Line + shaded band** | Central tendency plus uncertainty across runs/models | The band's meaning (SD/SE/CI) cannot be stated |
| **Multi-scenario lines** | Scenario comparison; dual-encode with linestyle | More than ~5 scenarios |
| **Step plot** | Discrete state changes, unit commitment, dispatch | The underlying process is smooth |
| **Stacked area over time** | Generation/consumption mix evolving | Series cross often |
| **Dual-axis (twinx)** | Two differently-scaled quantities co-evolving | Ever, almost — the correlation can be manufactured by rescaling. Prefer two panels or standardised units |
| **State-coloured segmented series** | A time series coloured by operating regime (charging / discharging / deficit) | More than ~4 states |
| **Calendar heatmap** | Daily-scale pattern across a long record | Fewer than ~2 months |
| **Hour × day heatmap** | Simultaneous diurnal and seasonal structure — the standard energy-systems figure | The record is shorter than a season |
| **Gantt chart** | Scheduling, unit start/stop, project timelines | Continuous quantities |
| **Event-study plot** | Effect around an intervention, x = time relative to the event | No clean event timing |
| **Cumulative curve** | Accumulated capacity, emissions, adoption | Rates matter more than totals |
| **Kaplan–Meier survival curve** | Time-to-event with censoring | No censoring and no time-to-event structure |
| **Spectral / wavelet plot** | Periodicity and multi-scale structure | Non-stationary series without a wavelet treatment |
| **Horizon chart** | Many time series compared in little vertical space | Audience unfamiliar |
| **Autocorrelation plot** | Serial dependence structure | Non-time-indexed data |

## 6. Spatial — "it happens here"

| Chart | Can express | Do not use when |
|---|---|---|
| **Point map** | Discrete sites and their attributes (colour, size) | Points overlap heavily at the display scale |
| **Choropleth** | A value per administrative or grid region | Large-but-empty regions dominate visually |
| **Proportional symbol map** | Magnitude as symbol area — avoids the choropleth area bias | Symbols overlap severely |
| **Dual-encoded point map** | Colour = variable A, size = variable B | Either variable has low dynamic range |
| **Raster / field map** | Continuous surfaces (irradiance, wind speed, temperature) | The underlying data are point samples with large gaps |
| **Flow map** | Trade, migration, transmission, logistics between places | Too many origin–destination pairs |
| **Cartogram** | Area distorted by a value (population, GDP) | Geographic recognisability is essential |
| **Hexbin map / tile grid map** | Equal-area cells replacing real boundaries, removing area bias | Exact geography matters |
| **Transect / profile** | Marginal behaviour along latitude or longitude | Pattern is not zonally structured |
| **Map small multiples** | Several variables, one small map each | More than ~9 variables |
| **Inset map** | A magnified hotspot within a global view | No genuine hotspot |
| **Dot density map** | Count as randomly placed dots within regions | Readers may misread dot positions as real locations |

**Projection**: use Robinson or Equal Earth for global displays; use an equal-area
projection whenever areas are compared. Never Web Mercator for global statistics.
Remove the map frame.

## 7. Flow and network — "it moves / it connects"

| Chart | Can express | Do not use when |
|---|---|---|
| **Sankey** | Conserved flow of energy, material, or money through stages — **and** migration of entities between categories across scenarios or time | Flows are not conserved; more than ~4 stages |
| **Alluvial** | Recategorisation of the same entities across successive groupings | Categories are not mutually exclusive |
| **Chord diagram** | Bidirectional flow matrices (trade, migration OD); grouped nodes make the block structure readable | More than ~15 sectors — nobody can trace a ribbon end to end, and it becomes a texture. Aggregate to the groups, or use a Sankey (staged flow) or a heatmap matrix (the claim is "which pairs are large") |
| **Network graph** | Topology, community structure, centrality | Hairball density (>~500 edges without filtering) |
| **DAG** | Causal structure, Bayesian networks, confounder identification | Cycles exist |
| **Dendrogram** | Hierarchical clustering, phylogeny | The clustering is unstable |
| **Arc diagram** | Linear node ordering with connections above | Many long-range edges |
| **Flowchart** | Method steps, algorithm control flow | Decision logic is trivial |
| **Architecture diagram** | System components and data paths | Component names do not match the paper's section names |
| **PRISMA flow diagram** | Literature screening in a systematic review | Not a systematic review |
| **State transition diagram** | Finite states and permitted transitions | Continuous dynamics |

## 8. Uncertainty and inference — "how sure are we"

| Chart | Can express | Do not use when |
|---|---|---|
| **Error bars** | Mean ± SD / SE / CI — the caption must say which, and n | The definition cannot be stated |
| **Coefficient plot** | Regression β with CI; significance by colour or stars | Coefficients are on incomparable scales without standardisation |
| **Forest plot** | Pooled effect sizes across studies or subgroups | Fewer than ~4 estimates |
| **Partial regression (added-variable) plot** | The net relationship after controlling for other covariates | Simple bivariate context |
| **VIF / collinearity diagnostic** | Reliability of a multiple regression | Single predictor |
| **Tornado diagram** | One-at-a-time sensitivity, ranked by influence | Interactions dominate |
| **Sobol / variance-decomposition bars** | Global sensitivity: each factor's variance contribution | Model too expensive to sample adequately |
| **Monte-Carlo distribution with quantile bands** | Propagated uncertainty of a simulation | Only a point estimate exists |
| **Calibration plot** | Predicted probability vs observed frequency | Non-probabilistic predictions |
| **ROC curve** | Classifier discrimination across thresholds | Severe class imbalance — use PR instead |
| **Precision–recall curve** | Classifier performance under class imbalance | Balanced classes and ROC is conventional |
| **Confusion matrix heatmap** | The structure of classification errors | Binary case with only summary metrics needed |
| **Learning curve** | Performance vs training-set size; data sufficiency | Single training run |
| **Convergence / loss curve** | Optimisation dynamics | Not iterative |
| **Ablation bar chart** | Each component's contribution | Components interact strongly (then report combinations) |
| **Volcano plot** | Effect size vs significance across many features | Few features |
| **Manhattan plot** | Genome-wide association significance by position | Non-positional features |
| **SHAP beeswarm / feature importance** | Which features drive a model, and in which direction | Model is inherently interpretable and coefficients suffice |
| **Posterior distribution / trace plot** | Bayesian inference results and chain mixing | Frequentist analysis |
| **Gradient / equifinality plot** | Multiple parameter sets giving equally good fits | Unique optimum |

## 9. Concept and schematic — no data

| Figure | Can express | Paradigms | Tool |
|---|---|---|---|
| **Motivated example (Figure 1)** | A concrete real case where existing methods fail (red) and the proposed one succeeds (green) | Before/after; failure gallery; annotated real artefact | PowerPoint draft → Figma polish |
| **Solution overview** | How the method works, module by module | **Pipeline** (linear stages) / **System architecture** (interacting components, feedback) / **Multi-layer** (offline–online, train–infer) | draw.io, PowerPoint, TikZ |
| **System topology** | Physical device connectivity | Icon library plus flow arrows | Illustrator / PowerPoint + SVG icon set |
| **Conceptual framework** | 2×2 matrix, pyramid, cycle, nested spheres | — | PowerPoint |
| **Timeline** | Technology or policy evolution | — | PowerPoint |
| **Graphical abstract** | The whole paper in one image | — | Figma |
| **Study-design diagram** | Cohorts, arms, sampling, exclusions | — | draw.io |

**Iron rule for the solution overview**: every module name in the figure must match a
section heading in the text *word for word*. If the figure says "Hotspot Detector",
the paper must contain a section called "Hotspot Detector".

**Budget**: the motivated example deserves 1–2 full working days. Reviewers scan
Figure 1, the overview, and the main results figure in under a minute and decide from
those three whether the paper is worth reading carefully.
