# Map panels

Only relevant when the data carries coordinates. Everything here is optional for
a paper without them — see [composition.md](composition.md) §0 for which layout
templates need geography and which do not.

A map panel is the one chart type where writing it from scratch reliably
produces something both ugly and un-submittable, because the failure is
structural: the basemap is a large amount of ink encoding no variable, and it
will dominate the marks unless it is actively suppressed.

Code: [`assets/nature_map.py`](../assets/nature_map.py). Compact version of this
document: Step 3b of SKILL.md.

---

## 1. The layer stack

```
1  basemap     land / ocean / coastline / borders, all near-invisible
2  polygons    reference or administrative regions: outlined, or filled by value
3  field       a continuous surface: density, interpolation, raster
4  points      one mark per site, encoded by value
5  marginals   profiles along longitude / latitude beside the panel
```

Most maps need two or three. Using all five often means the panel is carrying
more than one claim — but check that before cutting, because a map missing the
layer a reader needs to orient themselves fails at the one job a map panel has.

```python
from nature_style import panel, apply_style, save_all
from nature_map import map_axes, value_points, add_colorbar

p = panel(placed_mm=120, aspect=0.5, draw_scale=2)
apply_style(p)
fig, ax = map_axes(p)                   # global Robinson; pass extent= for a region
sc = value_points(ax, lon, lat, value, spec=p)
add_colorbar(fig, ax, sc, 'Value (unit)', spec=p)
save_all('fig1_a_map', fig)
```

## 2. Points or polygons

Decided by the **unit of observation**, not by taste. If the data are sites, use
`value_points`. If the unit *is* the region — national statistics, model output
on zones — use `choropleth`. A choropleth of site averages silently encodes
region area, which is not a variable in the analysis.

## 3. The basemap preset: the single biggest lever

`BASEMAP` in `nature_map.py` ships defaults that keep the basemap subordinate to
the data. They are defaults, not a rule, and every key is overridable.

| | `global_points` | `published_linework` |
|---|---|---|
| land | `#E8E8E8` solid | `#CECECE` at alpha 0.2 → near-white |
| coastline | `#888888` hairline | `#1A1A1A` hairline |
| frame | on | **off** |
| graticule | off | **on, labelled** |

`global_points` **fills** the continents; `published_linework` **draws** them.
Filled land is a mid-grey mass that competes with the marks and swallows its own
grey coastline, so the continents lose their internal structure and the panel
reads flat. Near-white land with a near-black hairline coastline inverts that:
the basemap becomes a line drawing costing almost no visual weight, which leaves
the colour ramp all of the contrast. **Prefer `published_linework` for a global
point map**, especially under a dark ramp.

**Frame and graticule are a pair, not two independent switches.** A frame plus a
graticule on a Robinson panel gives you a stray octagon *and* labels colliding
with it at the curved edges; no frame plus a graticule gives the published look,
because the labels then sit in the whitespace the curve leaves behind. The
failure everyone has seen — degree labels piling up at both curved edges — is
caused by the frame, not by the globe. Do not mix the halves of a preset.

National borders default **on** in both global presets: they are the landmarks a
reader locates sites against. Turn them off for a continuous field, or where
they would themselves be read as data.

## 4. What makes marks read as published

- **Overlapping marks carry a thin dark ring.** It keeps a few hundred touching
  discs countable instead of letting them merge into a smear. It is worth
  nothing when marks do not touch, where it just darkens the panel and eats the
  contrast the colour ramp is carrying. `value_points(ring='auto')` switches it
  on above `RING_AUTO_N`; that threshold is a rule of thumb, so look at the panel.
- **Extremes are drawn last** so they are not buried under the bulk of the data.
- **The colormap is chosen from the data, not from habit.** `pick_cmap` returns
  a diverging ramp centred on the reference value when the variable straddles
  it, and a sequential ramp when it does not. It never returns a rainbow.
- **Region names belong to the text layer** — added at assembly, not in the script.

## 5. Two implementation traps

Both invisible until submission, both of which a first attempt walks into.

| Naive version | Why it fails | Instead |
|---|---|---|
| A per-point marker image (`OffsetImage`, or patches rendered to PNG in a loop) | Embeds one raster object per site into a file that must stay editable vector, and costs minutes for a few thousand sites | one vector `scatter` with `edgecolors` — same look, ~1 s |
| Nested loop over every point × every grid cell for a density field | ~10⁸ iterations for a few thousand sites | weighted `histogram2d` + `gaussian_filter` — same field, ~4 orders of magnitude faster |

## 6. The density field is optional and easy to make useless

Bandwidth below about half the spacing between clusters turns it into a halo
around each point, showing nothing the scatter did not. Threshold too low shades
the whole panel, which defeats the purpose — the layer exists to name the two or
three regions that dominate. Draw it, look at it, and delete it if it does not
change a conclusion.

## 7. Marginal profiles

They answer what the map cannot: which band along one axis carries the
magnitude. Worth adding whenever the claim contains a gradient; skip otherwise.

## 8. Which layer to turn ON — the addition pass

`map_axes` defaults are tuned for a global site map. Change them deliberately.
This table is the map-specific half of SKILL.md Step 3d.

| Layer | Turn it ON when | Leave it OFF when |
|---|---|---|
| **National borders** (`borders=True`, default) | the reader must locate individual sites, or the caption names countries | the panel shows a continuous field, or borders would be misread as data |
| **Heavier coastline** (`coastline_weight=1.5–2`) | coastline *is* the subject — archipelago, coastal process, small regional extent | a global panel where the hairline default already separates land from sea |
| **Frame** (`frame=`, preset) | the map sits beside framed panels, or the projection edge would otherwise be invisible | a Robinson global panel with a graticule — the box becomes a stray octagon; an inset; sibling panels all frameless |
| **Graticule** (`grid=`, or `graticule(ax)`) | the land is near-white and carrying no frame, so nothing else gives the panel structure; a regional panel; the claim refers to latitude or longitude bands | over solid grey land, where it is a fourth grey layer nobody reads |
| **Graticule labels** (`labels=`, preset) | whenever the graticule is on and the frame is off | alongside a frame, where they collide with it at the curved edges |
| **Higher coastline resolution** (`'50m'`, `'10m'`) | the extent is continental or national | a global panel — wasted file size at print resolution |
| **Marginal profile** | the claim contains a gradient along one axis | the claim is about discrete clusters |
| **Inset** | one region carries the result and is unreadable at global scale | no genuine hotspot |

## 9. Projection

Robinson or Equal Earth for global displays; an equal-area projection whenever
areas are compared. Never Web Mercator for global statistics. Remove the map
frame unless the preset keeps it (§3).
