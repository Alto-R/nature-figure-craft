# Quadrant and region plots

A quadrant plot is not a scatter with two lines drawn on it. It is a
**classifier displayed over a scatter**. The points are evidence that the
classes are populated; the payload is the partition. Everything below follows
from that one sentence, and most bad quadrant figures are bad because the
author treated the lines as decoration on a scatter rather than as the claim.

The test for whether you have understood which figure you are making: **if you
deleted the points and kept the lines and fills, would the panel still say
something?** If yes, it is a region plot and this document applies. If no — if
the interesting thing is the shape of the cloud, the slope, the outliers — then
the two lines are clutter and you want a plain scatter with a smoother.

Code: [`assets/nature_quadrant.py`](../assets/nature_quadrant.py). Every rule
below has a function behind it.

---

## 1. When it earns its place, and when it does not

**Use it when** the paper needs a *vocabulary*. The classes become nouns the
abstract can use, the colours propagate to every later panel — bars, maps,
flow diagrams — and the reader stops needing a legend after Figure 2. That
propagation is the entire return on the figure, and it is large.

**Do not use it when:**

| Situation | What is wrong | Instead |
|---|---|---|
| The dividing lines cannot be named | The figure asserts a classification the data does not support | Plain scatter |
| The claim is about the *relation* (slope, correlation, trade-off) | Binning a continuous relation into four boxes throws away the thing being claimed | Scatter + LOWESS, or a parity plot |
| One class holds 90% of the observations | The partition is not partitioning | One threshold, or a different variable pair |
| Most classes are empty | The scheme is finer than the data | Fewer classes, or fold the empty ones |
| n is small (< ~20) | Class counts are noise; one point moves the headline | Report the values, not the classes |

**Discretising costs information, always.** That cost is worth paying when the
classes get reused elsewhere in the paper and not otherwise. If the quadrant
scheme appears exactly once, in the panel that defines it, it did not earn the
information it destroyed.

## 2. Where the dividing lines come from

This is the part a reviewer attacks, and rightly: move a line and the headline
number moves with it. Four families, in descending order of how much defending
they need.

| Family | Examples | What has to be stated |
|---|---|---|
| **Definitional** | `y = x` break-even, zero, a published standard, a regulatory limit | Nothing beyond naming it. The strongest kind of line — it is not an estimate |
| **Model-derived** | Two-component mixture crossing, changepoint, Otsu, a fitted cluster boundary | The evidence that the structure exists: ΔBIC, a likelihood ratio, a silhouette |
| **Distributional** | Median, tertile, a stated quantile | The statistic, its value, and n. Plus a sensitivity check (§2.2) |
| **Eyeballed** | "About here looks right" | Never use one. If you cannot name the rule, the classification is an assertion |

**Each axis gets its own rule, and the two need not match.** A common and
entirely legitimate figure has a definitional diagonal, a median on one axis,
and a policy threshold on the other. Forcing all boundaries into one family
because it looks tidier is how a definitional line ends up presented as a
statistical convention, or worse, the reverse.

### 2.1 The model-derived line needs its evidence, not just its number

A mixture model always returns a boundary. Only the model-comparison statistic
says whether the data has two modes rather than one. ΔBIC = BIC(1) − BIC(2),
read conventionally: **< 2 no evidence, 2–6 weak, 6–10 strong, > 10 very
strong**. Below about 6, fall back to the median and say so. A model-derived
line with no model evidence behind it is an eyeballed line wearing a lab coat,
and it is worse than the median because it looks rigorous.

The number belongs in the caption, not in a supplementary table.

### 2.2 Sensitivity: the test that decides whether the figure is publishable

Recount every class under one or two *defensible alternative* lines — the 45th
and 55th percentile instead of the median, the 2-sigma instead of the 3-sigma
cut, the other reasonable standard.

- If the sentence the figure lets a reader state survives, report the
  classification and move on.
- If it flips, **the classification is not a finding** and the figure must not
  be built on it. This is not a reason to hunt for the threshold that gives the
  nicer answer.

`sensitivity()` does the recount. Run it before drawing, not after a reviewer
asks.

### 2.3 The shared-threshold case

Using *one* number as the line on both axes is legitimate only when the axes
carry the same units and the comparison across them is meaningful — cost
against price, one year's value against another's. Then say so explicitly,
because a reader who assumes two independently derived medians will read the
class counts wrongly. When the units differ, a shared number is a coincidence
of scaling and means nothing.

## 3. The partition need not be a 2×2

Two orthogonal thresholds give four rectangles. Adding a diagonal gives up to
six regions; a curved feasibility boundary gives whatever it gives. The general
object is not a grid, it is a **function** `classify(x, y) → class name`.

That framing pays off three times:

1. **The background is the classifier evaluated on a grid.** No rectangle
   arithmetic, no re-derivation when a boundary moves, and — the real point —
   the fill can never disagree with the classification the statistics used,
   because they are the same code path. (`region_background`.)
2. **Any boundary shape works.** Diagonals, curves, and conditional rules
   ("high cost only matters when infeasible") compose as predicates.
3. **The legend is the same function** rendered on a blank pair of axes (§9),
   so it cannot drift either.

**Ceiling: about six non-empty classes.** Beyond that the reader is memorising
a codebook, and the vocabulary benefit that justified the figure disappears.

**Unreachable and empty classes are results, not bugs.** A scheme that admits
"feasible, high cost, low affordability" and finds nobody there is telling you
something. Report it as an explicit zero (`counts_table` lists empties on
purpose) and decide deliberately whether to fold it into a neighbour. What you
must not do is quietly drop it from the legend — a six-region scheme rendered
with five colours and no explanation is a reader's unanswerable question.

## 4. Naming the classes

**Name the data condition, never the screen position.** "Top right" does not
survive an axis inversion, and a "low is good" axis gets inverted routinely.
"High cost, unviable" survives everything.

**Words, not `Q1`–`Q4` alone.** `Q1` is a handle for the text to refer back to;
it is not a name. If the classes are worth a figure they are worth six words
each, and those words are what the reader repeats to a colleague. Pair them if
you like — `Q1: viable, low cost` — but the words carry the load.

The names should be the same strings in the figure, the legend, the caption,
the table of counts and the abstract. Not paraphrases. Define them once in the
code and import that definition everywhere, the same discipline the semantic
colour dictionary gets.

## 5. Colour and layering

**Ordered classes get an ordered ramp; nominal classes get a pale nominal
set.** If the scheme runs best → worst, a qualitative palette throws away the
one thing a reader could have read off the fill without consulting anything.

**The fill is background.** Keep alpha in the 0.15–0.3 range. Above ~0.35 it
competes with the marks, and on an ordered ramp it starts reading as a
continuous surface, which it is not.

**Budget the colour channel once.** The regions have already spent colour. If
the points also carry a colour scheme — group, region, category — the two must
be separable by construction: saturated marks on desaturated fills, or
desaturated marks on pale fills. Two mid-saturation schemes in one panel is the
most common way a quadrant figure becomes unreadable, and no amount of style
fixing rescues it.

Worked fill/mark pairs are in [palettes.md](palettes.md) §9 and importable as
`REGION_FILL` / `REGION_MARK`. Their construction is the point: every mark is its
own region's hue at higher saturation and 15–35 L\* darker, so a mark always reads
as belonging to its region *and* always clears it — while the fills stay within
8 L\* of each other, so no region looks more important than another. For a ranked
partition use the ordered ramp (§4.2) instead; four independent hues would discard
the rank.

**Z-order**, bottom to top:

```
0  region fill
1  grid, if any (usually none — the dividing lines are the structure)
3  marks
4  dividing lines
6  labels
```

Dividing lines sit **above** the marks by default: a divider that vanishes
under a dense cloud has stopped doing its job, and it is the thing the panel is
about. Drop it below only when the claim concerns individual points sitting
near the line.

**Two line colours, deliberately.** A definitional line is part of the claim
and takes an accent colour; a distributional line is a convention the reader is
being asked to accept and takes neutral grey. Drawing both identically tells
the reader they have equal standing, which is the most common way a quadrant
figure overstates itself.

## 6. Encoding a third variable

Area (bubbles) or point colour, not both.

- **Area** must be proportional to the value, which means mapping the value's
  **square root** to the marker diameter. Mapping it to diameter directly
  inflates the largest mark quadratically and is a misrepresentation, not a
  style choice.
- Set an explicit size range and keep it identical across panels that will be
  compared. A bubble legend with two or three reference sizes belongs in the
  standalone legend file.
- **Draw large marks first** so small ones land on top. Otherwise the panel
  quietly loses its smallest class — usually the interesting one.
- Above a few hundred marks, bubbles stop being readable as area. Use uniform
  small marks and put the third variable in a companion panel.

## 7. Marginal distributions

A histogram or KDE along the top and right is not decoration here. It is
**where the reader checks the dividing line**. A median through the peak of a
unimodal marginal is a convention; the same line through a trough is a finding,
and the marginal is the only place that difference is visible.

Rules:

- Bins computed over the **main panel's limits**, not the data range, so bars
  align with the ticks below them. A misaligned marginal reads as a second,
  unrelated figure.
- No frame, no ticks, no axis labels. Its axis is the panel's axis.
- Height ~15–25% of the panel. Larger and it competes; smaller and it is a smear.
- Carry the dividing line into the marginal when the line's placement is the
  argument.

Skip them when the claim is purely about class membership and the thresholds
are definitional — there is nothing to check.

## 8. Insets

An inset earns its place when the mass genuinely concentrates: as a rule of
thumb, **~90% of observations inside ~20% of the axis range**. Otherwise it is
a second copy of the same picture.

The step people skip: **the inset must repeat the region background and the
dividing lines.** Magnified points stripped of the classification that gives
them meaning make the reader work out which class they are looking at, and at
that zoom the boundaries are usually outside the window, so they cannot. Draw
the source rectangle on the main panel, keep the connectors short by placing
the inset near the region it magnifies, and give the inset a thin frame — it is
a different coordinate system and must look like one.

## 9. The legend is a miniature of the scheme, not a list of swatches

The highest-leverage single move available in this figure family.

A column of colour chips beside four or six phrases asks the reader to hold the
phrases in working memory and match them to fills. A **thumbnail of the
partition itself** — same classifier, same colours, dividing lines drawn, axes
blank, each class labelled inside its own region — teaches the entire scheme at
a glance, including the *geometry*, which a swatch list cannot express at all.

Generate it by calling the same `classify` function (`partition_legend`), so it
cannot drift from the analysis when a threshold moves. Export it as its own
file and place it during assembly, in whatever whitespace the layout leaves.

## 10. What the caption must contain

1. The rule and the value for **every** dividing line — "vertical line: global
   median cost, 0.34 USD kWh⁻¹; diagonal: break-even, price = cost".
2. n per class, or a pointer to the table that has it.
3. What area and colour encode, with units.
4. For a model-derived line, the evidence statistic.
5. If an axis is inverted, say so — readers assume it is not.

## 11. Failure table

| Symptom | Cause | Fix |
|---|---|---|
| Reviewer asks "why there?" | Line has no stated rule | §2; state it in the caption |
| Class counts change when the threshold moves slightly | The classification is noise | §2.2; do not publish it as a finding |
| Reader cannot tell the classes apart | Fill and mark colour at similar saturation | §5; desaturate one of the two |
| Panel looks like a scatter with stray lines | Fill alpha too low, or no fill | Raise to 0.2–0.3 |
| Fill reads as a heatmap | Alpha too high, ordered ramp too smooth | Lower alpha; widen the steps |
| A colour in the panel is missing from the legend | Empty class silently dropped | §3; report the zero |
| Legend takes longer to read than the panel | Swatch list | §9; draw the scheme |
| Largest bubble dominates everything | Value mapped to diameter, not to area | §6; square-root the value |
| Inset is unreadable | Background and dividers not repeated | §8 |
| Labels hide the marks they annotate | Everything labelled | Label only what the claim points at |

## 12. Handoff

The class definitions, the thresholds and their provenance strings, and the
colour dictionary are **one object used by four consumers**: the main panel,
the legend, the statistics in the text, and every later figure that reuses the
classes. Define them once, in one module, and import. The moment a threshold is
retyped in a second file, the paper has two classifications and no way to know
which one the numbers came from.
