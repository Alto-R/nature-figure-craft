# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). While the version is
0.x, a minor release may change behaviour; every such change is listed here.

## [Unreleased]

## [0.2.0] - 2026-11-03

### Changed

- **Licensing split.** Code (`*.py`, `*.R`, tests, workflows) is now under the
  MIT License; documentation and skill content (`SKILL.md`, `references/`,
  READMEs) stay under CC BY 4.0, now in `LICENSE-docs`. Creative Commons
  advises against CC licenses for software. Releases up to and including
  0.1.0 remain available under CC BY 4.0.
- `nature_chord.R` no longer uses extrafont. The PNG preview now renders through
  cairo as well, so it shows what the PDF will show.

### Fixed

- `nature_chord.R`: the exported PDF rendered every label as garbage in real
  viewers (PDFium, Ghostscript, MuPDF) while the PNG preview looked correct.
  `pdf()` with an extrafont-registered Arial embedded no font program, and the
  AFM that Rttf2pt1 generates wrote zero widths for space and hyphen. Both
  export sites now use `cairo_pdf()`, which embeds Arial as a TrueType subset.
  Without cairo, export falls back to `pdf()` with base-14 Helvetica.
  ([#1](https://github.com/Alto-R/nature-figure-craft/issues/1), reported by
  @iMiku)

### Added

- Continuous integration (GitHub Actions): lint, the Python test suite on
  Linux, Windows and macOS (Python 3.9 and 3.13), and an R job that runs the
  chord diagram and checks every font in its PDFs is embedded.
- Test suite in `tests/`: each self-test still runs and writes its files, the
  style module's PDF keeps text as embedded TrueType, `profile_data.py`
  detects geo / time / facet / tail structure, and the chord regression test
  for #1.
- `CONTRIBUTING.md`, issue templates and a pull-request template.
- This changelog, and a release workflow that publishes each tag's section of
  it as a GitHub release.
- `requirements.txt` / `requirements-dev.txt`.
- Pre-submission checklist (`references/workflow.md`): check that every font
  in the PDF is embedded, and read the PDF itself, not only the PNG preview.

## [0.1.0] - 2026-08-28

First public release. Tagged retroactively on commit `a4362ec`, the last
commit of the release day.

### Added

- `chart-type-chooser` skill: chart catalogue (~70 types across nine
  communicative intents), decision rules, anti-pattern guide, and
  `profile_data.py`, which profiles a data file before any chart is proposed.
- `nature-figure-production` skill: final-artwork specification, house style,
  palette gallery, multi-panel composition templates, map and region-plot
  recipes, panel-separated production workflow and pre-submission checklist.
- Plotting modules: `nature_style.py` (landed-size type, palettes, export),
  `nature_panels.py` (panel recipe gallery: distributions, coefficients,
  compositions, fits, densities, state timelines, matrices), `nature_map.py`,
  `nature_quadrant.py`, and `nature_chord.R`.
- Bilingual README (Chinese and English).

[Unreleased]: https://github.com/Alto-R/nature-figure-craft/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Alto-R/nature-figure-craft/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Alto-R/nature-figure-craft/releases/tag/v0.1.0
