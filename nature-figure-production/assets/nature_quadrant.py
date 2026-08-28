"""
nature_quadrant.py -- region ("quadrant") plots for journal figures.

A quadrant plot is not a scatter with two lines drawn on it. It is a
**classifier displayed over a scatter**: the payload is the partition of the
plane into named classes, and the points are evidence that the classes are
populated. Every design decision in this module follows from that.

Usage
-----
    from nature_style import panel, apply_style, save_all
    from nature_quadrant import (threshold, regions, region_background,
                                 divider, bubble_scatter, marginal_axes,
                                 marginal_dist, counts_table)

    tx = threshold(df.cost,  "median")        # -> value + a caption string
    ty = threshold(df.price, "median")

    part = regions([
        ("Viable, low cost",   lambda x, y: y >= x and x <= tx.value),
        ("Viable, high cost",  lambda x, y: y >= x),
        ("Unviable, low cost", lambda x, y: x <= tx.value),
    ], default="Unviable, high cost", colors=RAMP_ORDERED)

    p = panel(placed_mm=90, aspect=0.85)
    apply_style(p)
    fig, ax = plt.subplots(figsize=p.figsize)
    region_background(ax, part, xlim, ylim)
    divider(ax, x=tx.value, y=ty.value, diagonal=True, spec=p)
    bubble_scatter(ax, df.cost, df.price, size=df.flow, spec=p)
    print(counts_table(part, df.cost, df.price))
    save_all("fig2_a_quadrant", fig)

Design rules encoded here
-------------------------
* The partition is a **function**, not four rectangles. `Partition.classify`
  takes (x, y) and returns a class name; the background is that same function
  evaluated on a grid. Straight lines, diagonals, curves and unreachable
  regions all fall out for free, and the background can never disagree with
  the classification used in the statistics -- they are the same code path.
* Class names are **words about the data condition**, never "Q1" and never a
  screen position. Axes get inverted at assembly; "top right" does not survive
  that, "high cost, unviable" does.
* Every dividing line carries its provenance as a string, because the caption
  has to state where the line came from. `threshold()` returns that string
  next to the number so the two cannot drift apart.
* Geometry (marker sizes, line widths, label offsets) scales with `spec` the
  same way `nature_style` and `nature_map` scale theirs, so a panel shrunk at
  assembly keeps its intended weight.

Dependencies: numpy + matplotlib. `gmm_threshold` additionally needs
scikit-learn; `marginal_dist(kde=True)` additionally needs scipy. Both degrade
with a clear message rather than failing late.

Nothing here depends on a specific project or discipline.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle

__all__ = [
    "RAMP_ORDERED", "RAMP_ORDERED_4", "PALE_NOMINAL", "DIVIDER", "BREAKEVEN",
    "Threshold", "threshold", "gmm_threshold", "sensitivity",
    "Partition", "regions", "quadrants",
    "region_background", "divider", "bubble_scatter",
    "marginal_axes", "marginal_dist", "zoom_inset", "label_points",
    "counts_table", "partition_legend",
]


# --------------------------------------------------------------------------
# Colour
#
# A partition whose classes are ORDERED (best -> worst, safe -> exposed) must
# get an ordered ramp; a qualitative palette throws away the one thing the
# reader could have read off the fill. A partition whose classes are merely
# different gets a pale nominal set instead.
#
# Both sets below are worked examples of the PATTERN -- one dict, defined once,
# reused in every panel and in the legend -- not recommended colours. Replace
# the values with your own.
# --------------------------------------------------------------------------

# Ordered, six classes, best -> worst. Blue end = desirable, red end = not.
RAMP_ORDERED = ["#012A61", "#0B75B3", "#89CAEA", "#F0D2D2", "#DC5654", "#982B2D"]

# Ordered, four classes.
RAMP_ORDERED_4 = ["#0B75B3", "#89CAEA", "#F0D2D2", "#DC5654"]

# Nominal, four classes. Pale on purpose: the fill is background, and the
# points and their own colour scheme have to stay legible on top of it.
PALE_NOMINAL = ["#d5e8f1", "#a9d9bb", "#f6dfd6", "#cfcce3"]

DIVIDER = "#444444"     # threshold lines: neutral, dashed
BREAKEVEN = "#be1420"   # a definitional line (y = x, zero, a standard): red


def _scale_of(spec) -> float:
    return getattr(spec, "draw_scale", 1.0) if spec is not None else 1.0


# --------------------------------------------------------------------------
# Where the dividing lines come from
#
# This is the part of a quadrant plot that a reviewer attacks, so the number
# and the rule that produced it travel together.
# --------------------------------------------------------------------------


class Threshold:
    """A dividing line: its value, the rule that produced it, and a caption.

    `caption` is written to be pasted into a figure caption verbatim. If you
    find yourself constructing a Threshold by hand with rule='eyeballed', the
    figure is asserting a classification the data does not support -- see
    references/quadrant.md.
    """

    __slots__ = ("value", "rule", "caption", "detail")

    def __init__(self, value, rule, caption, detail=None):
        self.value = float(value)
        self.rule = rule
        self.caption = caption
        self.detail = detail or {}

    def __float__(self):
        return self.value

    def __repr__(self):
        return f"Threshold({self.value:.6g}, rule={self.rule!r})"


def threshold(values, rule: str = "median", q: float = None,
              value: float = None, unit: str = "", fmt: str = ".3g") -> Threshold:
    """Derive one dividing line from data, keeping its provenance attached.

    rule
        'median'   -- the default, and the only distributional rule that needs
                      no further defence when the distribution is unimodal.
        'mean'     -- only when the quantity is symmetric; a mean threshold on
                      a skewed variable puts the line inside the tail.
        'quantile' -- with q=; use when the claim is about a minority
                      ("the worst decile"), not to manufacture a balanced split.
        'value'    -- with value=; a definitional or policy number. The
                      strongest kind of line: it needs no statistics at all.
    """
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    if a.size == 0 and rule != "value":
        raise ValueError("threshold(): no finite values")

    u = f" {unit}" if unit else ""
    if rule == "median":
        v = float(np.median(a))
        cap = f"median = {v:{fmt}}{u} (n = {a.size})"
    elif rule == "mean":
        v = float(np.mean(a))
        cap = f"mean = {v:{fmt}}{u} (n = {a.size})"
    elif rule == "quantile":
        if q is None:
            raise ValueError("rule='quantile' needs q=")
        v = float(np.quantile(a, q))
        cap = f"{q:.0%} quantile = {v:{fmt}}{u} (n = {a.size})"
    elif rule == "value":
        if value is None:
            raise ValueError("rule='value' needs value=")
        v = float(value)
        cap = f"fixed at {v:{fmt}}{u}"
    else:
        raise ValueError(f"unknown rule {rule!r}")
    return Threshold(v, rule, cap, {"n": int(a.size)})


def _two_gaussian_intersections(w1, m1, s1, w2, m2, s2):
    """Where two weighted 1-D Gaussian densities cross. Analytic, no search."""
    eps = 1e-12
    s1, s2 = max(float(s1), eps), max(float(s2), eps)
    a = -1.0 / (2 * s1 * s1) + 1.0 / (2 * s2 * s2)
    b = m1 / (s1 * s1) - m2 / (s2 * s2)
    c = (-m1 * m1 / (2 * s1 * s1) + m2 * m2 / (2 * s2 * s2)
         + np.log((w1 / s1) / (w2 / s2)))
    if abs(a) < 1e-14:
        return [float(-c / b)] if abs(b) > 1e-14 else []
    disc = b * b - 4 * a * c
    if disc < -1e-12:
        return []
    r = np.sqrt(max(0.0, disc))
    return sorted([float((-b + r) / (2 * a)), float((-b - r) / (2 * a))])


def gmm_threshold(values, positive_only: bool = False, seed: int = 0,
                  n_init: int = 10, unit: str = "", fmt: str = ".3g") -> Threshold:
    """Split point between two Gaussian components, with the evidence for two.

    Fits a 1-component and a 2-component Gaussian mixture and reports
    dBIC = BIC(1) - BIC(2). The threshold is where the two weighted component
    densities cross, between the component means.

    **dBIC is the number that licenses the figure, and it belongs in the
    caption.** A GMM will always return a boundary; only a positive dBIC says
    the data actually has two modes rather than one. Conventional reading:
    dBIC < 2 is no evidence, 2-6 weak, 6-10 strong, > 10 very strong. Below
    about 6, fall back to `threshold(..., 'median')` and say so -- a
    model-derived line with no model evidence behind it is an eyeballed line
    wearing a lab coat.
    """
    try:
        from sklearn.mixture import GaussianMixture
    except ImportError as e:      # pragma: no cover
        raise ImportError(
            "gmm_threshold() needs scikit-learn; use threshold(..., 'median') "
            "if you would rather not add the dependency") from e

    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    if positive_only:
        a = a[a > 0]
    if a.size < 20:
        raise ValueError(f"gmm_threshold(): n = {a.size} is too small to "
                         "distinguish one component from two")
    x = a.reshape(-1, 1)

    kw = dict(covariance_type="full", random_state=seed, n_init=n_init,
              reg_covar=1e-6)
    g1 = GaussianMixture(n_components=1, **kw).fit(x)
    g2 = GaussianMixture(n_components=2, **kw).fit(x)
    dbic = float(g1.bic(x) - g2.bic(x))

    mu = g2.means_.reshape(-1)
    sd = np.sqrt(np.maximum(g2.covariances_.reshape(-1), 1e-12))
    w = g2.weights_.reshape(-1)
    lo, hi = np.argsort(mu)

    roots = _two_gaussian_intersections(w[lo], mu[lo], sd[lo],
                                        w[hi], mu[hi], sd[hi])
    between = [r for r in roots if mu[lo] < r < mu[hi]]
    if between:
        v, how = between[0], "component crossing"
    else:
        v, how = float(np.mean(mu)), "midpoint of component means (no crossing)"

    u = f" {unit}" if unit else ""
    cap = (f"two-component Gaussian mixture, {how} = {v:{fmt}}{u} "
           f"(dBIC = {dbic:.1f}, n = {a.size})")
    return Threshold(v, "gmm", cap,
                     {"delta_bic": dbic, "means": mu.tolist(),
                      "sigmas": sd.tolist(), "weights": w.tolist(),
                      "n": int(a.size)})


def sensitivity(build_partition, x, y, alternatives, labels=None):
    """Recount the classes under alternative dividing lines.

    `build_partition(*args)` returns a Partition; `alternatives` is a list of
    argument tuples, the first of which should be the one you intend to
    publish. Returns a list of (label, {class: count}).

    The point is not to find a better threshold. It is to find out whether the
    sentence the figure lets a reader state survives a defensible change of
    line. If "most cases fall in the worst class" flips when the median moves
    to the 45th percentile, the classification is not a finding and the figure
    should not be built on it.
    """
    out = []
    for i, args in enumerate(alternatives):
        args = args if isinstance(args, (tuple, list)) else (args,)
        part = build_partition(*args)
        lab = labels[i] if labels else " / ".join(f"{a:.4g}" if
                                                  isinstance(a, (int, float))
                                                  else str(a) for a in args)
        out.append((lab, part.counts(x, y)))
    return out


# --------------------------------------------------------------------------
# The partition itself
# --------------------------------------------------------------------------


class Partition:
    """A named classification of the plane.

    names   : class names, in the order they should appear in a legend. For an
              ordered scheme that order is best -> worst, and the colour ramp
              must follow it.
    colors  : one colour per name.
    classify: f(x, y) -> name, for scalar x and y.
    """

    __slots__ = ("names", "colors", "classify", "_index")

    def __init__(self, names, classify, colors=None):
        self.names = list(names)
        if colors is None:
            colors = (RAMP_ORDERED if len(self.names) > 4 else RAMP_ORDERED_4)
        colors = list(colors)
        if len(colors) < len(self.names):
            raise ValueError(f"{len(self.names)} classes but {len(colors)} colours")
        self.colors = colors[:len(self.names)]
        self.classify = classify
        self._index = {n: i for i, n in enumerate(self.names)}

    def color(self, name) -> str:
        return self.colors[self._index[name]]

    def ids(self, x, y) -> np.ndarray:
        """Class index per observation. -1 for anything the classifier misses."""
        f = np.vectorize(self.classify, otypes=[object])
        named = f(np.asarray(x, dtype=float), np.asarray(y, dtype=float))
        return np.array([self._index.get(n, -1) for n in np.ravel(named)]
                        ).reshape(np.shape(named))

    def counts(self, x, y) -> dict:
        ids = self.ids(x, y)
        return {n: int(np.sum(ids == i)) for i, n in enumerate(self.names)}

    def __repr__(self):
        return f"Partition({len(self.names)} classes: {', '.join(self.names)})"


def regions(rules, default: str, colors=None) -> Partition:
    """Build a Partition from ordered (name, predicate) rules; first match wins.

    This is the general constructor, and the reason the module does not model
    quadrants as rectangles: a rule is any predicate, so a diagonal break-even
    line, a curved feasibility boundary and a plain median split all compose
    without new geometry code.

        part = regions([
            ("Viable, low cost",  lambda x, y: y >= x and x <= t),
            ("Viable, high cost", lambda x, y: y >= x),
        ], default="Unviable", colors=RAMP_ORDERED_4)

    Ordering matters twice over: it decides which rule wins an overlap, and it
    is the legend order. Write the rules so that reading them top to bottom
    reads as the argument the figure is making.
    """
    names = [n for n, _ in rules] + [default]
    preds = list(rules)

    def classify(x, y):
        for name, pred in preds:
            if pred(x, y):
                return name
        return default

    return Partition(names, classify, colors)


def quadrants(x_split, y_split, names=None, colors=None) -> Partition:
    """The plain 2x2 case.

    `names` is given in READING order -- top-left, top-right, bottom-left,
    bottom-right -- and named for the DATA CONDITION each corner represents,
    not for the corner. Axes get inverted at assembly (a "low is good" axis
    routinely is); a name like "high x, low y" survives that and "top right"
    does not.
    """
    xs, ys = float(x_split), float(y_split)
    if names is None:
        names = ("Low x, high y", "High x, high y",
                 "Low x, low y", "High x, low y")
    if len(names) != 4:
        raise ValueError("quadrants() takes exactly four names")
    tl, tr, bl, br = names

    def classify(x, y):
        if y >= ys:
            return tr if x >= xs else tl
        return br if x >= xs else bl

    return Partition([tl, tr, bl, br], classify,
                     colors if colors is not None else PALE_NOMINAL)


# --------------------------------------------------------------------------
# Drawing
# --------------------------------------------------------------------------


def region_background(ax, part: Partition, xlim=None, ylim=None,
                      alpha: float = 0.25, n: int = 400, zorder: float = 0):
    """Fill the panel with the partition, by evaluating it on a grid.

    Not by drawing rectangles. Rectangles have to be re-derived by hand every
    time a boundary moves and they silently disagree with the classifier the
    statistics used; a grid evaluation cannot, because it *is* the classifier.
    Cost is one vectorised call over n x n points.

    `alpha` stays low on purpose. The fill is context; the marks are data. Much
    above ~0.35 the background starts competing with the point colours, and on
    an ordered ramp it also starts reading as a continuous surface, which it is
    not.
    """
    xlim = tuple(xlim if xlim is not None else ax.get_xlim())
    ylim = tuple(ylim if ylim is not None else ax.get_ylim())
    xx, yy = np.meshgrid(np.linspace(min(xlim), max(xlim), n),
                         np.linspace(min(ylim), max(ylim), n))
    z = part.ids(xx, yy).astype(float)
    cmap = mcolors.ListedColormap(part.colors)
    ax.contourf(xx, yy, z, levels=np.arange(-0.5, len(part.colors)),
                cmap=cmap, alpha=alpha, zorder=zorder,
                antialiased=True)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    return z


def divider(ax, x=None, y=None, diagonal=None, spec=None,
            color=None, diagonal_color=BREAKEVEN, ls: str = "--",
            lw: float = 1.0, zorder: float = 4, label=None):
    """Draw the dividing lines, on top of the background.

    x, y      : threshold lines. Accepts a float or a Threshold.
    diagonal  : True for y = x, or (slope, intercept).

    Two colours on purpose. A **definitional** line -- y = x, zero, a published
    standard -- is part of the claim and gets the accent colour; a
    **distributional** line -- a median -- is a convention the reader is being
    asked to accept, and gets neutral grey. Drawing both in the same colour
    tells the reader the two have equal standing, which is the single most
    common way a quadrant figure overstates itself.

    `zorder` puts the lines above the points by default: a divider that
    disappears under a dense cloud has stopped doing its job. Drop it below the
    marks only when the claim is about individual points sitting near the line.
    """
    s = _scale_of(spec)
    color = color or DIVIDER
    out = []
    if x is not None:
        out.append(ax.axvline(float(x), color=color, ls=ls, lw=lw * s,
                              zorder=zorder, alpha=0.9))
    if y is not None:
        out.append(ax.axhline(float(y), color=color, ls=ls, lw=lw * s,
                              zorder=zorder, alpha=0.9))
    if diagonal is not None and diagonal is not False:
        slope, intercept = (1.0, 0.0) if diagonal is True else diagonal
        xl, yl = ax.get_xlim(), ax.get_ylim()
        xs = np.array([min(xl), max(xl)])
        out.append(ax.plot(xs, slope * xs + intercept, color=diagonal_color,
                           ls=ls, lw=lw * 1.3 * s, zorder=zorder,
                           label=label)[0])
        ax.set_xlim(*xl)
        ax.set_ylim(*yl)
    return out


def bubble_scatter(ax, x, y, size=None, color="#333333", spec=None,
                   size_range=(4.0, 14.0), scale: str = "sqrt",
                   edgecolor="white", edgewidth: float = 0.3,
                   alpha: float = 0.95, zorder: float = 3, **kw):
    """Points, optionally area-encoded by a third variable.

    scale : 'sqrt' (default) maps the variable to marker DIAMETER via its
        square root, so perceived AREA is proportional to the value. 'linear'
        maps it to area directly, which exaggerates large values -- correct
        only if you intend the figure to shout about the largest one. 'log'
        for a variable spanning orders of magnitude.

    Marks are drawn largest first, so small points end up on top and stay
    visible. Without that a bubble chart quietly loses its smallest class,
    which is usually the one the paper is about.

    `size_range` is in points of diameter and is multiplied by the panel's
    draw scale, so bubbles keep their weight when the panel is shrunk at
    assembly.
    """
    s = _scale_of(spec)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    lo, hi = size_range

    if size is None:
        d = np.full(x.shape, (lo + hi) / 2.0)
    else:
        v = np.asarray(size, dtype=float)
        if scale == "sqrt":
            t = np.sqrt(np.maximum(v - np.nanmin(v), 0))
        elif scale == "log":
            t = np.log10(np.maximum(v, np.nextafter(0, 1)))
            t = t - np.nanmin(t)
        elif scale == "linear":
            t = v - np.nanmin(v)
        else:
            raise ValueError(f"unknown scale {scale!r}")
        span = np.nanmax(t) if np.nanmax(t) > 0 else 1.0
        d = lo + (t / span) * (hi - lo)

    order = np.argsort(-d)                      # big first, small on top
    c = color
    if not isinstance(color, str):
        c = np.asarray(color, dtype=object)[order]

    return ax.scatter(x[order], y[order], s=(d[order] * s) ** 2,
                      c=c, alpha=alpha, zorder=zorder,
                      edgecolors=edgecolor, linewidths=edgewidth * s, **kw)


def marginal_axes(ax, size: str = "20%", pad: float = 0.04):
    """Attach a top and a right axes sharing the main panel's limits.

    Marginals on a quadrant plot are not decoration: they are where the reader
    checks whether a threshold sits in a valley of the distribution or in the
    middle of a mode. A median line through the peak of a unimodal marginal is
    a convention; the same line through a trough is a finding.
    """
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    div = make_axes_locatable(ax)
    ax_top = div.append_axes("top", size=size, pad=pad, sharex=ax)
    ax_right = div.append_axes("right", size=size, pad=pad, sharey=ax)
    for a in (ax_top, ax_right):
        a.set_facecolor("none")
        for sp in a.spines.values():
            sp.set_visible(False)
    ax_top.tick_params(labelbottom=False, bottom=False, left=False,
                       labelleft=False)
    ax_right.tick_params(labelleft=False, left=False, bottom=False,
                         labelbottom=False)
    return ax_top, ax_right


def marginal_dist(max_ax, values, orient: str = "x", bins=None, kde: bool = True,
                  color="#4a7db3", fill="#9abece", spec=None, alpha: float = 0.35):
    """Histogram + optional KDE on a marginal axes.

    orient : 'x' for the top marginal, 'y' for the right one.

    The bins are computed over the MAIN panel's limits, not over the data
    range, so the bars line up with the axis they sit above. A marginal whose
    bars are offset from the ticks below them reads as a second, unrelated
    figure.
    """
    s = _scale_of(spec)
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    lim = max_ax.get_xlim() if orient == "x" else max_ax.get_ylim()
    lo, hi = min(lim), max(lim)
    if bins is None:
        bins = np.histogram_bin_edges(v, bins="auto", range=(lo, hi))
    elif np.isscalar(bins):
        bins = np.linspace(lo, hi, int(bins) + 1)

    counts, edges = np.histogram(v, bins=bins, range=(lo, hi))
    centres = 0.5 * (edges[:-1] + edges[1:])
    width = np.diff(edges)

    if orient == "x":
        max_ax.bar(centres, counts, width=width, color=fill,
                   edgecolor="white", linewidth=0.3 * s, zorder=1)
    else:
        max_ax.barh(centres, counts, height=width, color=fill,
                    edgecolor="white", linewidth=0.3 * s, zorder=1)

    if kde and v.size > 2:
        try:
            from scipy import stats
        except ImportError:
            kde = False
        else:
            grid = np.linspace(lo, hi, 200)
            dens = stats.gaussian_kde(v)(grid)
            dens = dens * counts.max() / dens.max() if dens.max() > 0 else dens
            if orient == "x":
                max_ax.plot(grid, dens, color=color, lw=0.9 * s, zorder=2)
                max_ax.fill_between(grid, dens, color=color, alpha=alpha,
                                    lw=0, zorder=1)
            else:
                max_ax.plot(dens, grid, color=color, lw=0.9 * s, zorder=2)
                max_ax.fill_betweenx(grid, dens, color=color, alpha=alpha,
                                     lw=0, zorder=1)

    if orient == "x":
        max_ax.set_ylim(0, counts.max() * 1.15 if counts.max() else 1)
        max_ax.set_yticks([])
    else:
        max_ax.set_xlim(0, counts.max() * 1.15 if counts.max() else 1)
        max_ax.set_xticks([])
    return counts, edges


def zoom_inset(ax, bounds, xlim, ylim, part: Partition = None, spec=None,
               dividers: dict = None, alpha: float = 0.25,
               mark: bool = True, connectors=(1, 3), frame_color="#333333"):
    """An inset over a sub-rectangle of the panel, carrying the same partition.

    bounds : [x0, y0, w, h] in axes fraction -- where the inset sits.
    xlim, ylim : the data window it magnifies.
    part, dividers : redraw the background and the lines inside the inset.

    That redraw is the whole point and is the step people skip. An inset
    showing bare points, magnified out of the classification that gives them
    meaning, makes the reader work out for themselves which class they are
    looking at -- and the answer is usually invisible at that zoom, because
    the dividing lines are outside the window.

    An inset earns its place when the mass genuinely concentrates: as a rule of
    thumb, when ~90% of observations fall inside ~20% of the axis range.
    Otherwise it is a second copy of the same picture.
    """
    s = _scale_of(spec)
    axin = ax.inset_axes(bounds)
    axin.set_xlim(*xlim)
    axin.set_ylim(*ylim)
    if part is not None:
        region_background(axin, part, xlim, ylim, alpha=alpha)
    if dividers:
        divider(axin, spec=spec, **dividers)
    axin.set_xticks([])
    axin.set_yticks([])
    for sp in axin.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.5 * s)
        sp.set_edgecolor(frame_color)

    if mark and connectors:
        # draws the source rectangle AND the leader lines, in one object
        ax.indicate_inset_zoom(axin, edgecolor=frame_color, alpha=0.8,
                               lw=0.4 * s)
    elif mark:
        ax.add_patch(Rectangle((min(xlim), min(ylim)),
                               abs(xlim[1] - xlim[0]), abs(ylim[1] - ylim[0]),
                               fill=False, edgecolor=frame_color,
                               lw=0.5 * s, zorder=5))
    return axin


def label_points(ax, x, y, labels, spec=None, fontsize=None, mask=None,
                 offset: float = 8.0, iterations: int = 200,
                 leader_color="#666666", leader_lw: float = 0.3,
                 min_leader: float = 6.0):
    """Direct labels with a small deterministic repulsion pass.

    No randomness and no seed: the same inputs give the same layout on every
    run, which matters when a figure is regenerated during revision and the
    co-authors are comparing it against the version they annotated.

    `mask` labels a subset. Use it. Labelling every point in a crowded panel
    produces a wall of text that hides the marks it is annotating; label what
    the claim actually points at, and let the rest be a distribution.

    This is a light-touch repeller: it separates overlapping labels and keeps
    them inside the axes, and it is not a match for adjustText or ggrepel on a
    genuinely dense panel. If labels still collide, label fewer of them --
    that is the better fix anyway.
    """
    s = _scale_of(spec)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    labels = np.asarray(labels, dtype=object)
    idx = np.arange(x.size) if mask is None else np.flatnonzero(np.asarray(mask))
    if idx.size == 0:
        return []

    fs = fontsize if fontsize is not None else \
        (getattr(spec, "tick", 9.0) if spec is not None else 8.0) * s
    off = offset * s

    texts = [ax.text(x[i], y[i], str(labels[i]), fontsize=fs, ha="center",
                     va="center", zorder=6,
                     transform=ax.transData) for i in idx]

    fig = ax.figure
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()

    # Label boxes are measured ONCE: their size does not change when they move,
    # so the whole relaxation runs in display coordinates as array arithmetic
    # rather than as one canvas redraw per iteration.
    boxes = np.array([[t.get_window_extent(rend).width,
                       t.get_window_extent(rend).height] for t in texts])
    half = boxes / 2.0 + 1.0 * s                    # half-extent plus a hair

    anchors = ax.transData.transform(np.column_stack([x[idx], y[idx]]))
    home = anchors + np.array([0.0, off])
    pos = home.copy()

    # every point repels, not just the labelled ones -- a label parked on an
    # unlabelled mark hides data just as effectively as one on a labelled mark
    pts = ax.transData.transform(np.column_stack([x, y]))
    pr = 3.0 * s                                    # assumed mark radius, px

    ab = ax.get_window_extent(rend)

    for _ in range(iterations):
        move = np.zeros_like(pos)
        busy = np.zeros(pos.shape[0], dtype=bool)

        # --- label vs label: separate along the axis of LEAST penetration,
        # which is what stops a pair from sliding past each other sideways
        dx = pos[:, None, 0] - pos[None, :, 0]
        dy = pos[:, None, 1] - pos[None, :, 1]
        ox = (half[:, None, 0] + half[None, :, 0]) - np.abs(dx)
        oy = (half[:, None, 1] + half[None, :, 1]) - np.abs(dy)
        hit = (ox > 0) & (oy > 0)
        np.fill_diagonal(hit, False)
        if hit.any():
            sx = np.sign(dx)
            sx[sx == 0] = 1.0
            sy = np.sign(dy)
            sy[sy == 0] = 1.0
            use_x = ox <= oy
            px = np.where(hit & use_x, sx * ox * 0.6, 0.0)
            py = np.where(hit & ~use_x, sy * oy * 0.6, 0.0)
            move[:, 0] += px.sum(axis=1)
            move[:, 1] += py.sum(axis=1)
            busy |= hit.any(axis=1)

        # --- label vs point
        pdx = pos[:, None, 0] - pts[None, :, 0]
        pdy = pos[:, None, 1] - pts[None, :, 1]
        pox = (half[:, None, 0] + pr) - np.abs(pdx)
        poy = (half[:, None, 1] + pr) - np.abs(pdy)
        phit = (pox > 0) & (poy > 0)
        if phit.any():
            sy = np.sign(pdy)
            sy[sy == 0] = 1.0
            move[:, 1] += np.where(phit & (poy <= pox), sy * poy * 0.35,
                                   0.0).sum(axis=1)
            sx = np.sign(pdx)
            sx[sx == 0] = 1.0
            move[:, 0] += np.where(phit & (poy > pox), sx * pox * 0.35,
                                   0.0).sum(axis=1)
            busy |= phit.any(axis=1)

        if not np.any(np.abs(move) > 0.25 * s):
            break

        # The pull back to the source point applies only to labels that are
        # currently clear. Applying it to a colliding label balances the
        # separation force and parks the pair at the overlap they started with.
        step = np.clip(move, -6.0 * s, 6.0 * s)
        pull = np.where(busy[:, None], 0.0, 0.06 * (home - pos))
        pos = pos + step + pull
        pos[:, 0] = np.clip(pos[:, 0], ab.x0 + half[:, 0], ab.x1 - half[:, 0])
        pos[:, 1] = np.clip(pos[:, 1], ab.y0 + half[:, 1], ab.y1 - half[:, 1])

    inv = ax.transData.inverted()
    for t, p, a in zip(texts, pos, anchors):
        t.set_position(inv.transform(p))
        if np.hypot(*(p - a)) > min_leader * s:
            x0, y0 = inv.transform(a)
            x1, y1 = t.get_position()
            ax.plot([x0, x1], [y0, y1], color=leader_color,
                    lw=leader_lw * s, zorder=5, solid_capstyle="round")
    return texts


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def counts_table(part: Partition, x, y, total: bool = True) -> str:
    """Class counts and shares, formatted for the caption and the text.

    A quadrant figure that does not report n per class is asking the reader to
    estimate it by counting dots. Every class in the partition is listed --
    including the empty ones, because a class that the scheme admits and the
    data never reaches is itself a result, and silently dropping it from the
    legend is how a six-region scheme turns into an unexplained five-colour one.
    """
    counts = part.counts(x, y)
    n = sum(counts.values())
    w = max(len(k) for k in counts) if counts else 0
    lines = [f"{k.replace(chr(10), ' '):<{w}}  {v:5d}  "
             f"{(v / n * 100 if n else 0):5.1f}%"
             + ("   (empty)" if v == 0 else "")
             for k, v in counts.items()]
    if total:
        lines.append(f"{'total':<{w}}  {n:5d}")
    return "\n".join(lines)


def partition_legend(part: Partition, xlim=(0, 1), ylim=(0, 1),
                     dividers: dict = None, figsize=(2.4, 2.4),
                     alpha: float = 0.6, fontsize: float = 6.5,
                     annotate: bool = True, axis_labels=None):
    """The legend as a miniature of the scheme itself, not a list of swatches.

    This is the highest-leverage single move in a quadrant figure. A colour
    swatch next to the words "Viable, high cost" makes the reader hold four or
    six phrases in their head and match them to fills. A thumbnail of the
    partition -- same classifier, same colours, dividing lines drawn, axes
    blank -- teaches the whole scheme at a glance and, because it calls the
    same `classify`, cannot drift from the analysis when a threshold moves.

    Export it as its own file (`export_legend` in nature_style, or save_all on
    the returned figure) and place it during assembly, in the whitespace the
    layout leaves.
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    region_background(ax, part, xlim, ylim, alpha=alpha)
    if dividers:
        divider(ax, **dividers)
    if annotate:
        # place each label at the centroid of its own class, found the same
        # way the background is: by evaluating the classifier on a grid.
        n = 200
        xs = np.linspace(min(xlim), max(xlim), n)
        ys = np.linspace(min(ylim), max(ylim), n)
        xx, yy = np.meshgrid(xs, ys)
        ids = part.ids(xx, yy)
        for i, name in enumerate(part.names):
            m = ids == i
            if not m.any():
                continue
            ax.text(xx[m].mean(), yy[m].mean(), name, ha="center", va="center",
                    fontsize=fontsize, color="#1A1A1A", zorder=4,
                    linespacing=1.25)
    ax.set_xticks([])
    ax.set_yticks([])
    if axis_labels:
        ax.set_xlabel(axis_labels[0])
        ax.set_ylabel(axis_labels[1])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    return fig, ax


# --------------------------------------------------------------------------
# Self-test: synthetic data only, no project files.
# --------------------------------------------------------------------------

if __name__ == "__main__":
    rng = np.random.default_rng(7)
    n = 260
    cost = np.abs(rng.lognormal(-1.0, 0.7, n))
    price = np.abs(cost * rng.lognormal(0.15, 0.6, n))
    weight = rng.lognormal(3, 1.2, n)

    tx = threshold(cost, "median", unit="USD kWh-1")
    print("x divider:", tx.caption)

    def build(xs):
        return regions([
            ("Viable\nlow cost",   lambda x, y, xs=xs: y >= x and x <= xs),
            ("Viable\nhigh cost",  lambda x, y, xs=xs: y >= x),
            ("Unviable\nlow cost", lambda x, y, xs=xs: x <= xs),
        ], default="Unviable\nhigh cost", colors=RAMP_ORDERED_4)

    part = build(tx.value)
    print(counts_table(part, cost, price))

    print("\nsensitivity to the dividing line:")
    for lab, c in sensitivity(build, cost, price,
                              [(tx.value,), (np.quantile(cost, .45),),
                               (np.quantile(cost, .55),)],
                              labels=["median", "45th pct", "55th pct"]):
        print(f"  {lab:<10}", {k.replace(chr(10), ' '): v for k, v in c.items()})

    xlim = (0, float(np.quantile(cost, 0.99)))
    ylim = (0, float(np.quantile(price, 0.99)))

    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    region_background(ax, part, xlim, ylim)
    divider(ax, x=tx.value, diagonal=True)
    bubble_scatter(ax, cost, price, size=weight, color="#1f3b57")
    ax.set_xlabel("Cost (USD kWh$^{-1}$)")
    ax.set_ylabel("Price (USD kWh$^{-1}$)")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    top, right = marginal_axes(ax)
    marginal_dist(top, cost, "x")
    marginal_dist(right, price, "y")
    fig.savefig("demo_quadrant.png", dpi=200, bbox_inches="tight")

    figl, _ = partition_legend(part, dividers=dict(x=0.5, diagonal=True))
    figl.savefig("demo_quadrant_legend.png", dpi=200, bbox_inches="tight")

    # --- second panel: plain 2x2, labels, and a zoom inset ----------------
    ty = threshold(price, "median")
    q = quadrants(tx.value, ty.value,
                  names=("Low cost, high price", "High cost, high price",
                         "Low cost, low price", "High cost, low price"))
    fig2, ax2 = plt.subplots(figsize=(4.6, 4.0))
    region_background(ax2, q, xlim, ylim)
    divider(ax2, x=tx.value, y=ty.value)
    bubble_scatter(ax2, cost, price, color="#1f3b57", size_range=(3, 8))
    biggest = weight > np.quantile(weight, 0.96)
    label_points(ax2, cost, price, [f"s{i}" for i in range(n)], mask=biggest)
    zx = (0.0, 2 * tx.value)
    zy = (0.0, 2 * ty.value)
    axin = zoom_inset(ax2, [0.55, 0.55, 0.42, 0.42], zx, zy, part=q,
                      dividers=dict(x=tx.value, y=ty.value))
    bubble_scatter(axin, cost, price, color="#1f3b57", size_range=(3, 8))
    axin.set_xlim(*zx)
    axin.set_ylim(*zy)
    ax2.set_xlabel("Cost (USD kWh$^{-1}$)")
    ax2.set_ylabel("Price (USD kWh$^{-1}$)")
    fig2.savefig("demo_quadrant_2x2.png", dpi=200, bbox_inches="tight")

    try:
        bimodal = np.concatenate([rng.normal(0, 1, 400), rng.normal(5, 1, 400)])
        print("\nGMM:", gmm_threshold(bimodal).caption)
        print("GMM on a single mode:",
              gmm_threshold(rng.normal(0, 1, 800)).caption)
    except ImportError as e:
        print("\nGMM skipped:", e)

    print("\nwrote demo_quadrant.png, demo_quadrant_legend.png, "
          "demo_quadrant_2x2.png")
