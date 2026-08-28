# Final artwork specification

Source: *Nature branded research journals: Guide to preparing final artwork*.
Applies to Nature, Nature Communications, and the Nature-branded research journals.
Other publishers (Elsevier, IEEE, Science) differ in numbers but not in kind — check
the target journal, then substitute.

## Table of contents

1. Governing principle
2. Figure widths
3. Figure heights
4. Typography
5. Colour mode
6. Vector vs raster
7. Mixed figures
8. Assembly and file limits
9. Office software
10. Photoshop
11. Special content
12. Third-party imagery
13. Most common rejections

---

## 1. Governing principle

> Figures should be prepared **at the size they will be displayed when published**,
> not arbitrarily enlarged or reduced.

Every downstream rule follows from this. Decide the physical size first; type size,
line weight, and marker size are then expressed in final printed units.

Where artwork does not meet the standard, the journal's art editor may redraw it into
house style — which means losing control over how the result looks.

## 2. Figure widths

### Original research and review content

Applies to: Analysis, Article, Brief Communication, Consensus Statement, Hypothesis,
Letter, Perspective, Progress Article, Resource, Review Article, Technical Report.

| Type | Width |
|---|---:|
| Single column | **88 mm** |
| Double column | **180 mm** |

In inches (matplotlib `figsize`):

```python
MM = 1 / 25.4
SINGLE_COL = 88  * MM   # 3.4646 in
DOUBLE_COL = 180 * MM   # 7.0866 in
```

### Other content types

| Type | Width |
|---|---:|
| Single column | 58 mm |
| Double column | 121 mm |
| Triple column | 185 mm |

## 3. Figure heights

Maximum height is coupled to caption length, because the two share the page.

| Caption length | Max height, single column | Max height, double column |
|---|---:|---:|
| < 300 words | ~130 mm | ~185 mm |
| < 150 words | ~180 mm | ~210 mm |
| < 50 words | ~220 mm | ~225 mm |

Practical consequence: a tall, dense main figure forces a short caption. If the figure
needs a 300-word caption to be understandable, it is doing too much — split it.

## 4. Typography

- **Sans-serif only**. Recommended: **Helvetica** or **Arial**.
- **Minimum 5 pt, maximum 7 pt** — measured at final printed size.
- Axis labels, tick labels, legends, panel letters, and in-figure annotations must all
  fall inside that window and remain legible.
- Text should stay **editable**, not flattened into pixels.

Matplotlib implication: `pdf.fonttype = 42` and `ps.fonttype = 42` embed TrueType and
keep glyphs as text. The default (Type 3) converts text to outlines. For SVG,
`svg.fonttype = 'none'` keeps text as text.

Panel-letter size is the one place to exceed body type slightly (8 pt bold is
conventional and accepted).

## 5. Colour mode

| Content type | Colour mode |
|---|---|
| Original research content | **RGB** |
| Perspective, Progress Article, Review Article, other non-research | CMYK |

Matplotlib emits RGB by default, which is correct for research articles. Only convert
to CMYK if the target content type requires it, and do the conversion in Illustrator.

## 6. Vector vs raster

### Must be vector

Graphs, charts, schematics, line art, maps, flow diagrams, model diagrams, anything
built from lines, text, and symbols.

Accepted formats: **AI**, **EPS**, **PDF**.

Requirements:
- Exported directly from the originating software (matplotlib → PDF, not
  matplotlib → PNG → "PDF").
- Text, data, lines, and colours remain editable.

Not accepted as final vector artwork: BMP, GIF, GIMP, JPG, PNG, Tex, TIFF.

### May be raster

Photographs, complex technical illustrations, 3D-rendered graphics, micrographs.

Requirements:
- **≥ 300 dpi** at final printed size.
- Use the highest-quality original file available.
- Never upsample in Photoshop — resampling adds pixels, not information.

## 7. Mixed figures

A figure combining raster and vector content — arrows over a micrograph, a scale bar
over a photo, axes over a raster basemap, labels on a 3D render — must keep the two
layers separate.

- Raster component: ≥ 300 dpi, or the original resolution.
- Text, arrows, lines, axes, boxes, and scale bars: **independent editable vector
  objects layered on top**.
- Do not flatten everything into a single uneditable image.

The official guide illustrates this explicitly as a correct/incorrect pair.

## 8. Assembly and file limits

Recommended assembly software (vector-capable): **Adobe Illustrator**, **PDF**,
**PowerPoint**.

Not accepted for final assembly: BMP, GIF, GIMP, JPG, PNG, Tex, TIFF.

- All text and overlaid elements in the assembled figure must remain editable.
- Lines, arrows, axes, scale bars, and text boxes must be vector objects.
- Raster components placed at 300 dpi or original resolution.
- **Keep each final figure file under 50 MB.**

The 50 MB cap is the practical reason to use `rasterized=True` on very large scatter
layers: 100,000 vector circles will blow past it.

## 9. Office software

**Word** — not recommended for producing final artwork. Layers and vector formats can
degrade or flatten during import/paste.

**Excel** — charts must be converted to **PDF**. Screenshots of Excel charts are not
acceptable.

**PowerPoint** — acceptable, provided every element in the figure remains fully
editable.

**Graphic effects** — do not apply drop shadow, 3D rotate, bevel, or other complex
effects. They can be rasterised at low resolution on export.

## 10. Photoshop

Not recommended for scientific figures: it is raster-based, produces oversized files,
flattens vector data, and leaves the production team unable to edit.

If Photoshop / PSD / TIFF / EPS must be used:
- Text must remain editable **type layers**.
- Line art, charts, and symbols must remain **vector smart objects**.
- Do not flatten to a single image layer.

## 11. Special content

**Chemical structures** — if a composite figure is not `.cdx` but contains ChemDraw
structures, supply the separate `.cdx` file as well, formatted with the journal's
chemical-structure template.

**Stereo images** — submit at final print size in the accepted version.

## 12. Third-party imagery

- Every non-original image must state its source and carry publication permission.
- Images downloaded from the internet may not be used unless clearly under an
  appropriate **Public Domain** licence.
- The guide explicitly recommends **avoiding Wikimedia and Flickr**, because
  attribution and rights information there is frequently missing or unreliable.
- For stock/photo-library images: do **not** purchase them yourself. Supply the
  catalogue number and a low-resolution placeholder; the journal obtains rights and
  the final file.
- **BioRender** figures must be declared on the Third Party Rights form, including
  whether only a free-trial plan was used.

## 13. Most common rejections

| Problem | Requirement |
|---|---|
| Charts submitted as PNG/JPG | Must be AI/EPS/PDF vector |
| Text too large or too small | 5–12 pt landed; house target 9–10.5 pt body (the guide itself asks 5–7 — see SKILL.md Step 0) |
| Final figure assembled in Word | Not recommended; layers flatten |
| Screenshot of an Excel chart | Export to PDF instead |
| All Photoshop layers merged | Text and line art must stay editable |
| Arrows / scale bars flattened onto a micrograph | Must be independent vector objects |
| dpi artificially increased | Does not improve quality |
| Image downloaded from the web | Not permitted without a correct Public Domain licence |
| BioRender used without declaration | Third Party Rights form required |

## Condensed standard

```text
size close to final published size
Arial or Helvetica
5-12 pt type (house target 9-10.5)
RGB for original research
AI / EPS / PDF vector for charts, schematics, maps
>= 300 dpi for photographs and complex renders
all text, arrows, axes, scale bars remain editable
nothing flattened
no low-resolution PNG/JPG as final artwork
third-party rights cleared
<= 50 MB per figure file
```
