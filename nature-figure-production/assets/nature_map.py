# SPDX-FileCopyrightText: 2026 Churui Huang
# SPDX-License-Identifier: MIT

"""
nature_map.py -- publication map panels: basemap, polygons, points, fields.

A map panel is assembled from at most five layers, drawn in this order. Most
maps need two or three of them; using all five is usually a sign the panel is
carrying more than one claim.

    1  basemap        land / ocean / coastline / borders, quiet enough to sit
                      behind the data but present enough to locate it
    2  polygons       administrative or reference regions: outlined, or filled
                      by value (choropleth)
    3  field          a continuous surface: density, interpolation, raster
    4  points         one mark per site, encoded by value
    5  marginals      profiles along longitude / latitude beside the panel

    from nature_style import panel, apply_style, save_all
    from nature_map import map_axes, value_points, add_colorbar

    p = panel(placed_mm=120, aspect=0.5, draw_scale=2)
    apply_style(p)
    fig, ax = map_axes(p)                       # global Robinson by default
    sc = value_points(ax, lon, lat, value, spec=p)
    add_colorbar(fig, ax, sc, 'Value (unit)', spec=p)
    save_all('fig1_a_map', fig)

Everything is a parameter. The basemap defaults come from BASEMAP_PRESETS. They
are presets, not derivations, and switching preset is expected.

    use_basemap('published_linework')   # near-white land, dark hairline
                                        # coastline, no frame, labelled
                                        # graticule

Two implementation notes, because both are things a first attempt gets wrong and
both are invisible until submission:

* Points are ONE vector `scatter`. Drawing per-point marker images (via
  `OffsetImage`, or a loop of `Circle` patches rendered to PNG) embeds one raster
  object per site into a file the journal requires to stay editable vector, and
  costs minutes of runtime for a few thousand sites.
* The density field is a weighted 2-D histogram convolved with a Gaussian, not a
  loop over every point x every grid cell. Same field, ~4 orders of magnitude
  faster.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

__all__ = [
    "BASEMAP", "PALETTES", "pick_cmap",
    "BASEMAP_PRESETS", "use_basemap",
    "map_axes", "graticule", "polygon_overlay", "choropleth",
    "density_field", "value_points", "add_colorbar", "marginal_profile",
]

# --------------------------------------------------------------------------
# Colour
# --------------------------------------------------------------------------

PALETTES = {
    # Diverging -- use when zero (or a threshold) is a real reference point.
    "diverging": "RdBu_r",
    "diverging_warm": mpl.colors.LinearSegmentedColormap.from_list(
        "diverging_warm",
        ["#012f48", "#669aba", "#fbf0d9", "#be1420", "#7a0101"]),
    # Sequential -- use when the variable only goes low to high.
    "sequential": "viridis",
    "sequential_cvd": "cividis",
    "sequential_warm": "inferno",
    "density": "Blues",
}

# --------------------------------------------------------------------------
# Basemap presets
#
# These are PRESETS, not rules, and how much to trust them matters: each is one
# combination of values that is known to print well on a global point map. None
# is derived from a principle, and nothing about them generalises automatically
# to a regional map, a raster field, or another discipline's conventions.
#
# Keep one if it suits the panel, switch with
# use_basemap('minimal' | 'regional'), or override individual keys:
#
#     from nature_map import BASEMAP, use_basemap
#     use_basemap('regional')
#     BASEMAP['coastline'] = '#555555'      # one-off tweak
#
# Layer-visibility defaults (borders / frame / coastline_weight / resolution)
# live in the preset too, so switching a preset switches the whole look rather
# than just its colours. map_axes() reads them when its arguments are left None.
# --------------------------------------------------------------------------

BASEMAP_PRESETS = {
    # Quiet grey land, dotted national borders for landmarks, a hairline panel
    # frame. Land is a solid mid-light grey and the coastline is grey too, so
    # continents read as filled shapes rather than as outlines. Fine under a
    # light colour ramp; muddy under a dark one -- see 'published_linework'.
    "global_points": {
        "land": "#E8E8E8", "land_alpha": 1.0,
        "ocean": "#FFFFFF", "ocean_alpha": 1.0,
        "coastline": "#888888", "coastline_alpha": 0.8, "coastline_width": 0.4,
        "border": "#AAAAAA", "border_alpha": 0.6, "border_width": 0.3,
        "border_style": ":",
        "frame": "#9A9A9A", "frame_width": 0.4,
        "polygon_edge": "#666666",
        "graticule": "#AAAAAA",
        "profile": "#404040",
        # layer defaults
        "borders": True, "frame_on": True, "coastline_weight": 1.0,
        "graticule_on": False, "graticule_labels": False,
        "point_ramp": None,
        "resolution": "110m",
    },
    # The linework look. Four differences from 'global_points', and together
    # they are most of what "looks published" means on a global point panel:
    #
    #   land       near-white (#CECECE at alpha 0.2), not solid mid grey, so
    #              the basemap never competes with the marks
    #   coastline  near-black hairline, not grey -- the continents are drawn
    #              rather than filled, and the drawing is what survives being
    #              shrunk to 180 mm
    #   frame      OFF. The projection edge is implied by the graticule; a box
    #              round a Robinson panel reads as a stray octagon
    #   graticule  ON, with labels. It is the only structure left once the land
    #              is nearly white, and with no frame the labels have nothing
    #              to collide with at the curved edges.
    #
    # point_ramp is the same figure's five-stop ramp. It is NOT lightness
    # monotonic (dark blue -> cream -> dark red), so it reads as diverging even
    # when the variable is one-directional. That is a house choice inherited
    # with the look, not a perceptual recommendation: override it per panel if
    # the variable has no meaningful midpoint and a reader might infer one.
    # NOTE ON THE LINE WIDTHS. The source script drew at 14 x 6 in (355 mm) and
    # wrote lw=0.7 for the coastline, lw=0.5 for borders. Those are DRAWN widths
    # at a 355 mm canvas that lands on a 178 mm column -- i.e. landed 0.35 and
    # 0.25. Preset values here are landed (map_axes multiplies by draw_scale),
    # so they are halved rather than transcribed. Copying 0.7 straight across
    # doubles the coastline and turns the linework back into a grey smear,
    # which is the first thing this preset was supposed to fix.
    "published_linework": {
        "land": "#CECECE", "land_alpha": 0.2,
        "ocean": "#FFFFFF", "ocean_alpha": 1.0,
        "coastline": "#1A1A1A", "coastline_alpha": 0.5, "coastline_width": 0.35,
        "border": "#333333", "border_alpha": 0.3, "border_width": 0.25,
        "border_style": ":",
        "frame": "#9A9A9A", "frame_width": 0.4,
        "polygon_edge": "#555555",
        "graticule": "#AAAAAA",
        "profile": "#404040",
        "borders": True, "frame_on": False, "coastline_weight": 1.0,
        "graticule_on": True, "graticule_labels": True,
        "point_ramp": "diverging_warm",
        "resolution": "110m",
    },
    # Everything the data does not need. For panels that sit inside another
    # panel, or figures whose other panels are frameless.
    "minimal": {
        "land": "#EFEFEF", "land_alpha": 1.0,
        "ocean": "#FFFFFF", "ocean_alpha": 1.0,
        "coastline": "#9A9A9A", "coastline_alpha": 0.7, "coastline_width": 0.3,
        "border": "#BBBBBB", "border_alpha": 0.5, "border_width": 0.25,
        "border_style": ":",
        "frame": "#B0B0B0", "frame_width": 0.3,
        "polygon_edge": "#777777",
        "graticule": "#BBBBBB",
        "profile": "#505050",
        "borders": False, "frame_on": False, "coastline_weight": 1.0,
        "graticule_on": False, "graticule_labels": False,
        "point_ramp": None,
        "resolution": "110m",
    },
    # Continental or national extent: the coastline is doing structural work
    # and the hairline global default disappears at that scale.
    "regional": {
        "land": "#EDEDED", "land_alpha": 1.0,
        "ocean": "#FFFFFF", "ocean_alpha": 1.0,
        "coastline": "#6E6E6E", "coastline_alpha": 0.9, "coastline_width": 0.4,
        "border": "#9A9A9A", "border_alpha": 0.7, "border_width": 0.35,
        "border_style": ":",
        "frame": "#8A8A8A", "frame_width": 0.5,
        "polygon_edge": "#555555",
        "graticule": "#C4C4C4",
        "profile": "#404040",
        "borders": True, "frame_on": True, "coastline_weight": 1.6,
        "graticule_on": True, "graticule_labels": True,
        "point_ramp": None,
        "resolution": "50m",
    },
}

BASEMAP = dict(BASEMAP_PRESETS["global_points"])


def use_basemap(preset):
    """Switch the active basemap preset. Accepts a name or a dict of overrides."""
    if isinstance(preset, str):
        if preset not in BASEMAP_PRESETS:
            raise ValueError(f"unknown preset {preset!r}; "
                             f"have {sorted(BASEMAP_PRESETS)}")
        BASEMAP.clear()
        BASEMAP.update(BASEMAP_PRESETS[preset])
    else:
        BASEMAP.update(preset)
    return BASEMAP


# Above this many marks, value_points(ring='auto') switches the outline on.
# A rule of thumb for "they probably overlap at print size", not a measurement.
RING_AUTO_N = 200


def pick_cmap(values, diverging=None, center=0.0, robust=98):
    """Choose a colormap and norm from the data, not from habit.

    Returns (cmap, norm). If the values straddle `center`, the variable has a
    meaningful sign and gets a diverging ramp with the neutral colour pinned to
    `center` -- otherwise the reader cannot tell positive from negative without
    reading the colour bar. If they do not, it gets a sequential ramp.

    Rainbow ramps are never returned: they are perceptually non-uniform, invent
    boundaries that are not in the data, and fail for colour-blind readers.

    robust : clip the range to this central percentile. A diverging range is
        symmetric about `center`, so ONE extreme unit sets the range for
        everything and the other 95% of the map collapses into the neutral
        colour -- honest, but it shows nothing. Clipping puts the extremes
        out-of-range instead, which is why the colour bar should then be drawn
        with `extend='both'` so the reader knows values run past the ends.
        Pass robust=None for the true full range.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if not v.size:
        return PALETTES["sequential"], mpl.colors.Normalize()
    if diverging is None:
        tol = max(abs(v.max()), abs(v.min())) * 1e-6
        diverging = bool(v.min() < center - tol and v.max() > center + tol)

    if robust:
        lo = float(np.percentile(v, 100 - robust))
        hi = float(np.percentile(v, robust))
    else:
        lo, hi = float(v.min()), float(v.max())

    if diverging:
        half = max(abs(lo - center), abs(hi - center)) or 1.0
        return PALETTES["diverging"], mpl.colors.TwoSlopeNorm(
            vcenter=center, vmin=center - half, vmax=center + half)
    return PALETTES["sequential"], mpl.colors.Normalize(vmin=lo, vmax=hi)


def _scale_of(spec) -> float:
    return getattr(spec, "draw_scale", 1.0) if spec is not None else 1.0


# --------------------------------------------------------------------------
# Layer 1 -- basemap
# --------------------------------------------------------------------------


def map_axes(spec=None, figsize=None, projection=None, extent=None,
             land=True, ocean=True, coastline=True, borders=None,
             frame=None, coastline_weight=None, resolution=None, grid=None):
    """Figure + GeoAxes carrying the basemap.

    projection : a cartopy CRS, or a name ('Robinson', 'PlateCarree',
        'Mollweide', 'LambertConformal', ...). Default: Robinson for a global
        panel, PlateCarree when `extent` restricts it to a region.
    extent : (lon_min, lon_max, lat_min, lat_max) for a regional map; None for
        global.
    borders, frame, coastline_weight, resolution : default to the active preset
        (see BASEMAP_PRESETS). Pass a value to override for one panel.

        borders -- national borders. On in 'global_points' and 'regional': they
            give the reader landmarks to locate sites against, which is most of
            what a map panel is for. Turn off for a continuous field, or where
            the borders would themselves be read as data.
        frame -- panel outline. On in 'global_points' and 'regional'. Turn off
            when the map is an inset, or when sibling panels are frameless.
        coastline_weight -- multiplier on the preset coastline width. Raise it
            (1.5-2) when the coastline is the subject and the hairline default
            disappears; 'regional' already does this.
        resolution -- '110m' global, '50m' continental, '10m' national. Higher
            resolution on a small panel is wasted file size.
        grid -- draw the lon/lat graticule as part of the basemap. Off in
            'global_points', on in 'published_linework' and 'regional'. It is a
            preset key rather than a global rule because whether a graticule is
            clutter depends on the rest of the basemap: over solid grey land it
            is a fourth grey layer nobody reads, but over near-white land with
            no frame it is the only thing giving the panel structure.
    """
    if borders is None:
        borders = BASEMAP.get("borders", True)
    if frame is None:
        frame = BASEMAP.get("frame_on", True)
    if grid is None:
        grid = BASEMAP.get("graticule_on", False)
    if coastline_weight is None:
        coastline_weight = BASEMAP.get("coastline_weight", 1.0)
    if resolution is None:
        resolution = BASEMAP.get("resolution", "110m")
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    if projection is None:
        projection = ccrs.PlateCarree() if extent else ccrs.Robinson()
    elif isinstance(projection, str):
        projection = getattr(ccrs, projection)()

    if figsize is None:
        figsize = spec.figsize if spec is not None else (7.09, 3.2)
    s = _scale_of(spec)

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(1, 1, 1, projection=projection)
    ax.set_facecolor(BASEMAP["ocean"])

    if ocean:
        ax.add_feature(cfeature.OCEAN.with_scale(resolution),
                       facecolor=BASEMAP["ocean"],
                       alpha=BASEMAP["ocean_alpha"], zorder=0)
    if land:
        ax.add_feature(cfeature.LAND.with_scale(resolution),
                       facecolor=BASEMAP["land"],
                       alpha=BASEMAP["land_alpha"], zorder=0)
    if coastline:
        ax.add_feature(cfeature.COASTLINE.with_scale(resolution),
                       linewidth=BASEMAP["coastline_width"] * s * coastline_weight,
                       edgecolor=BASEMAP["coastline"],
                       alpha=BASEMAP["coastline_alpha"], zorder=1)
    if borders:
        ax.add_feature(cfeature.BORDERS.with_scale(resolution),
                       linestyle=BASEMAP["border_style"],
                       linewidth=BASEMAP["border_width"] * s,
                       edgecolor=BASEMAP["border"],
                       alpha=BASEMAP["border_alpha"], zorder=1)

    if extent:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
    else:
        ax.set_global()

    for name, sp in ax.spines.items():
        if name == "geo" and frame:
            sp.set_visible(True)
            sp.set_linewidth(BASEMAP["frame_width"] * s)
            sp.set_edgecolor(BASEMAP["frame"])
        else:
            sp.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.patch.set_visible(True)
    if grid:
        graticule(ax, spec)
    return fig, ax


def graticule(ax, spec=None, dlon=60, dlat=30, labels=None):
    """Dashed lon/lat graticule.

    labels defaults to the active preset's `graticule_labels` -- off in
    'global_points', on in 'published_linework' and 'regional'.

    The reason it is not simply "off for global panels": degree labels collide
    at the curved edges of a Robinson panel *when the panel has a frame*, which
    is what makes them look broken. Drop the frame, as 'published_linework'
    does, and the labels sit in the whitespace the curved edge leaves behind --
    which is where the whitespace left by the projection's curve already is.
    """
    import cartopy.crs as ccrs

    if labels is None:
        labels = BASEMAP.get("graticule_labels", False)
    s = _scale_of(spec)
    # draw_labels must be the SIDE LIST, not True-plus-`gl.right_labels = False`.
    # On a non-rectangular projection cartopy resolves the boolean attributes
    # against the projection edge rather than against a rectangle, and the
    # right/top suppressions are silently ignored -- you get 60 deg N printed
    # down both margins. Naming the sides up front is honoured on every
    # projection.
    sides = ["left", "bottom"] if labels is True else labels
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=sides or False,
                      linewidth=0.3 * s, color=BASEMAP["graticule"],
                      alpha=0.6, linestyle="--",
                      xlocs=range(-180, 181, dlon),
                      ylocs=range(-90, 91, dlat))
    if sides:
        size = mpl.rcParams["xtick.labelsize"]
        gl.xlabel_style = {"size": size, "color": "#404040"}
        gl.ylabel_style = {"size": size, "color": "#404040"}
    # Gridliner labels are drawn outside the axes but are not part of its
    # bbox, so a colour bar placed with the usual pad lands on top of them.
    # Flag it for add_colorbar rather than making every caller remember.
    ax._house_bottom_graticule = bool(sides) and "bottom" in sides
    return gl


# --------------------------------------------------------------------------
# Layer 2 -- polygons
# --------------------------------------------------------------------------


def _read_polygons(source):
    if hasattr(source, "iterrows"):
        return source
    import geopandas as gpd
    return gpd.read_file(source)


def polygon_overlay(ax, source, spec=None, edgecolor=None, facecolor="none",
                    linestyle="--", linewidth=None, label_column=None,
                    zorder=2):
    """Outline reference or administrative polygons over the basemap.

    Use for a regionalisation the reader needs in order to read the claim
    (climate zones, biogeographic regions, jurisdictions). Skip it if the claim
    does not refer to the regions -- outlines are expensive ink.

    label_column : draw each polygon's label at its largest part's centroid.
        Default None, because region names belong to the text layer and are
        normally placed at assembly, where the whole figure is visible.
    """
    import cartopy.crs as ccrs

    s = _scale_of(spec)
    polys = _read_polygons(source)
    if polys is None or len(polys) == 0:
        return polys

    ax.add_geometries(list(polys.geometry), crs=ccrs.PlateCarree(),
                      facecolor=facecolor,
                      edgecolor=edgecolor or BASEMAP["polygon_edge"],
                      linewidth=(0.4 * s) if linewidth is None else linewidth,
                      linestyle=linestyle, zorder=zorder)

    if label_column:
        for _, row in polys.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            if geom.geom_type == "MultiPolygon":
                geom = max(geom.geoms, key=lambda g: g.area)
            c = geom.centroid
            if geom.contains(c):
                ax.text(c.x, c.y, str(row[label_column]),
                        ha="center", va="center", weight="bold",
                        fontsize=mpl.rcParams["xtick.labelsize"],
                        transform=ccrs.PlateCarree(), zorder=zorder + 9)
    return polys


def choropleth(ax, source, column, spec=None, cmap=None, norm=None,
               center=0.0, edgecolor="white", linewidth=None, zorder=2,
               missing_color="#F2F2F2"):
    """Fill polygons by value.

    The right choice when the unit of observation IS the region -- national
    statistics, model output on a grid of zones. The wrong choice when the data
    are point sites: a choropleth of site averages silently encodes region area,
    which is not a variable in the analysis. Use value_points for sites.

    Returns a ScalarMappable suitable for add_colorbar.
    """
    import cartopy.crs as ccrs

    s = _scale_of(spec)
    polys = _read_polygons(source)
    v = polys[column].astype(float).values

    if cmap is None or norm is None:
        auto_cmap, auto_norm = pick_cmap(v, center=center)
        cmap = cmap or auto_cmap
        norm = norm or auto_norm
    cmap = plt.get_cmap(cmap) if isinstance(cmap, str) else cmap

    for geom, val in zip(polys.geometry, v):
        color = missing_color if not np.isfinite(val) else cmap(norm(val))
        ax.add_geometries([geom], crs=ccrs.PlateCarree(), facecolor=color,
                          edgecolor=edgecolor,
                          linewidth=(0.2 * s) if linewidth is None else linewidth,
                          zorder=zorder)

    sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array(v)
    return sm


# --------------------------------------------------------------------------
# Layer 3 -- continuous field
# --------------------------------------------------------------------------


def density_field(ax, lon, lat, values=None, spec=None, bandwidth=8.0,
                  resolution=1.0, levels=8, threshold_pct=90, clip_pct=99,
                  cmap=None, alpha=0.55, zorder=3):
    """Smoothed spatial density of the sites, optionally weighted by a value.

    Answers "which regions dominate", which an overplotted scatter cannot: the
    eye does not integrate overlapping marks.

    This layer is optional and easy to make useless. Two failure modes:

    * bandwidth too small (below roughly half the typical spacing between
      clusters) turns it into a halo around every point. It then shows nothing
      the scatter did not already show.
    * threshold too low shades the whole panel. The layer exists to name the two
      or three regions that dominate; if everything is shaded, nothing is.

    Defaults show roughly the top decile of occupied cells at a regional
    bandwidth. Try it, look at it, and delete it if it does not change a
    conclusion.

    bandwidth : Gaussian sigma in degrees.
    threshold_pct : percentile OF OCCUPIED CELLS below which cells are hidden.
        A percentile rather than a fraction of the peak, because real point
        distributions have one dominant cluster and a fraction-of-peak threshold
        masks every other region off the map.
    """
    import cartopy.crs as ccrs
    from scipy.ndimage import gaussian_filter

    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    w = np.ones_like(lon) if values is None else np.asarray(values, dtype=float)

    lons = np.arange(-180, 180 + resolution, resolution)
    lats = np.arange(-90, 90 + resolution, resolution)
    lon_edges = np.append(lons - resolution / 2, lons[-1] + resolution / 2)
    lat_edges = np.append(lats - resolution / 2, lats[-1] + resolution / 2)

    grid, _, _ = np.histogram2d(lat, lon, bins=[lat_edges, lon_edges], weights=w)
    grid = gaussian_filter(grid, sigma=bandwidth / resolution,
                           mode=("nearest", "wrap"))

    if grid.max() <= 0:
        return None
    threshold = np.percentile(grid[grid > 0], threshold_pct)
    mask = grid < threshold
    if mask.all():
        return None
    upper = np.percentile(grid[~mask], clip_pct)
    if not upper > threshold:
        return None

    lon_grid, lat_grid = np.meshgrid(lons, lats)
    return ax.contourf(
        lon_grid, lat_grid, np.ma.array(np.clip(grid, 0, upper), mask=mask),
        transform=ccrs.PlateCarree(), cmap=cmap or PALETTES["density"],
        norm=mpl.colors.Normalize(vmin=threshold, vmax=upper),
        levels=levels, alpha=alpha, zorder=zorder, extend="neither")


# --------------------------------------------------------------------------
# Layer 4 -- points
# --------------------------------------------------------------------------


def value_points(ax, lon, lat, values, spec=None, cmap=None, norm=None,
                 vmin=None, vmax=None, center=0.0,
                 size=6.0, size_range=None, ring="auto", ring_width=0.25,
                 zorder=10, rasterized=None):
    """One mark per site, coloured by value.

    ring : thin outline on every mark. Worth a lot when marks overlap -- it is
        what keeps a few hundred touching discs countable instead of letting
        them merge into a smear. Worth nothing when they do not, where it just
        darkens the panel and eats the colour contrast the ramp is carrying.

        'auto' (default) turns it on above RING_AUTO_N marks and off below,
        which is a crude proxy for "do these overlap"; pass a colour to force it
        on, or None to force it off. The threshold is a guess, not a finding --
        look at the panel and override it.
    size_range : (min, max) marker area to also encode value by size. Default
        None -- constant size. Double-encoding value as colour AND area survives
        greyscale printing and lets the eye find extremes before reading the
        colour bar, but it costs the reader a second decoding rule, so turn it
        on deliberately rather than by default.
    rasterized : default True above 5,000 marks, to keep the PDF under the
        journal's file-size cap. Everything else on the panel stays vector.
    """
    import cartopy.crs as ccrs

    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    v = np.asarray(values, dtype=float)
    s = _scale_of(spec)

    if cmap is None or norm is None:
        auto_cmap, auto_norm = pick_cmap(v, center=center)
        if cmap is None:
            # A preset may name a house ramp for one-directional variables.
            # It only applies when pick_cmap did NOT ask for a diverging ramp:
            # if the variable straddles the reference value, the neutral colour
            # has to sit at that value and a house ramp cannot honour that.
            house = BASEMAP.get("point_ramp")
            if house and auto_cmap != PALETTES["diverging"]:
                cmap = PALETTES.get(house, house)
            else:
                cmap = auto_cmap
        if norm is None:
            norm = auto_norm
    if vmin is not None or vmax is not None:
        norm = mpl.colors.Normalize(
            vmin=np.nanmin(v) if vmin is None else vmin,
            vmax=np.nanmax(v) if vmax is None else vmax)

    if size_range is None:
        sizes = np.full_like(v, float(size))
    else:
        lo, hi = norm.vmin, norm.vmax
        f = np.clip((v - lo) / (hi - lo), 0, 1) if hi > lo else np.zeros_like(v)
        sizes = size_range[0] + f * (size_range[1] - size_range[0])
    sizes = sizes * s ** 2

    if ring == "auto":
        ring = "#2b2b2b" if len(v) >= RING_AUTO_N else None

    order = np.argsort(v)  # extremes drawn last, so they are not hidden
    if rasterized is None:
        rasterized = len(v) > 5000

    return ax.scatter(lon[order], lat[order], c=v[order], s=sizes[order],
                      cmap=cmap, norm=norm, transform=ccrs.PlateCarree(),
                      edgecolors=ring if ring else "none",
                      linewidths=(ring_width * s) if ring else 0,
                      zorder=zorder, rasterized=rasterized)


def add_colorbar(fig, ax, mappable, label, spec=None, orientation="horizontal",
                 shrink=0.6, pad=None, aspect=40, extend="neither"):
    """Colour bar in house proportions, sized from the current style.

    pad : default 0.05, or 0.10 below a map whose graticule prints bottom
        labels -- those labels sit outside the axes bbox, so the usual pad puts
        the colour bar on top of them.
    """
    s = _scale_of(spec)
    if pad is None:
        pad = 0.10 if getattr(ax, "_house_bottom_graticule", False) else 0.05
    cbar = fig.colorbar(mappable, ax=ax, orientation=orientation,
                        shrink=shrink, pad=pad, aspect=aspect, extend=extend)
    cbar.set_label(label, fontsize=mpl.rcParams["axes.labelsize"])
    cbar.ax.tick_params(labelsize=mpl.rcParams["xtick.labelsize"],
                        width=0.6 * s, length=2.5 * s)
    cbar.outline.set_linewidth(0.4 * s)
    return cbar


# --------------------------------------------------------------------------
# Layer 5 -- marginal profiles
# --------------------------------------------------------------------------


def marginal_profile(ax, coord, values, axis="lon", spec=None, bin_width=None,
                     stat="median", smooth=True, color=None, fill=True,
                     min_n=1):
    """Binned statistic of `values` along longitude or latitude.

    Hung below or beside the map, this answers a question the map itself cannot:
    which band along one axis carries the magnitude. Worth adding whenever the
    claim contains a gradient ("concentrates at high latitude", "falls with
    distance from the equator"); skip it otherwise.

    axis : 'lon' -> runs left-right, plotted below the map.
           'lat' -> runs bottom-top, plotted to the side.
    stat : 'median' (default, robust) or 'mean'.
    min_n : minimum observations for a bin to be drawn. Bins below it are NaN
        and the line breaks across them, rather than being filled with zero --
        see the comment in the body. Raise it when the tails of the coordinate
        are sparse and a one-site bin would otherwise read as a real feature.
    """
    coord = np.asarray(coord, dtype=float)
    v = np.asarray(values, dtype=float)
    s = _scale_of(spec)
    color = color or BASEMAP["profile"]

    if axis == "lon":
        lo, hi, default_bin = -180.0, 180.0, 5.0
    elif axis == "lat":
        lo, hi, default_bin = -90.0, 90.0, 2.0
    else:
        raise ValueError("axis must be 'lon' or 'lat'")
    bw = default_bin if bin_width is None else bin_width

    edges = np.arange(lo, hi + bw, bw)
    centers = (edges[:-1] + edges[1:]) / 2
    idx = np.clip(np.digitize(coord, edges) - 1, 0, len(centers) - 1)
    f = np.median if stat == "median" else np.mean

    # A bin with too few observations is NOT a bin whose statistic is zero.
    # Filling empties with 0.0 draws a profile that dives to the axis wherever
    # there is no data, which a reader correctly reads as "the quantity is zero
    # here" -- the opposite of the truth. Empty and under-populated bins are
    # NaN, and the line is broken across them.
    counts = np.array([int(np.sum(idx == i)) for i in range(len(centers))])
    prof = np.array([f(v[idx == i]) if counts[i] >= min_n else np.nan
                     for i in range(len(centers))])
    good = ~np.isnan(prof)
    if not good.any():
        raise ValueError(f"no bin reaches min_n={min_n} at bin_width={bw}")

    if smooth and good.sum() > 3:
        from scipy.interpolate import make_interp_spline
        cg, pg = centers[good], prof[good]
        xs = np.linspace(cg.min(), cg.max(), 300)
        ys = np.maximum(make_interp_spline(cg, pg, k=3)(xs), 0)
        # do not let the spline bridge a gap wider than two bins
        gaps = np.diff(cg)
        for lo_c, g in zip(cg[:-1], gaps):
            if g > 2 * bw:
                ys[(xs > lo_c) & (xs < lo_c + g)] = np.nan
    else:
        xs, ys = centers, prof

    if axis == "lon":
        ax.plot(xs, ys, color=color, linewidth=0.9 * s)
        if fill:
            ax.fill_between(xs, 0, ys, where=~np.isnan(ys),
                            alpha=0.25, color=color, linewidth=0)
        ax.set_xlim(lo, hi)
        ax.set_ylim(0, None)
        ax.set_xticks([])
        for name in ("top", "right", "bottom"):
            ax.spines[name].set_visible(False)
    else:
        ax.plot(ys, xs, color=color, linewidth=0.9 * s)
        if fill:
            ax.fill_betweenx(xs, 0, ys, where=~np.isnan(ys),
                             alpha=0.25, color=color, linewidth=0)
        ax.set_ylim(lo, hi)
        ax.set_xlim(0, None)
        ax.set_yticks([])
        for name in ("top", "right", "left"):
            ax.spines[name].set_visible(False)
    return ax
