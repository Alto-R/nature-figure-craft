# Contributing to nature-figure-craft

Thanks for considering a contribution. This repository is two Claude Code
skills (`chart-type-chooser`, `nature-figure-production`) plus the plotting
modules they use. Most of it grew out of real manuscript figures, so the most
valuable contributions are the same kind of thing: a rule that broke on a real
figure, a recipe that held up in a real submission, a bug found by actually
exporting something.

## Reporting a problem

Open an issue with the **Bug report** template. A report is actionable when it
has:

- **what happened**, against what you expected, with the exact message if there
  is one;
- **environment**: OS, Python or R version, and the versions of matplotlib or
  circlize involved. For font problems, also say which fonts are installed and
  how;
- **a minimal reproduction**: ideally the module's own self-test, or a few lines
  on synthetic data;
- **what you already tried.**

For anything about exported artwork, **open the PDF itself, not only the PNG**.
The PNG is a preview, and some failures show up only in the deliverable.
[#1](https://github.com/Alto-R/nature-figure-craft/issues/1) is an example: the
chord diagram's PNG was correct while its PDF rendered as garbage. That issue
is also a model report.

## Proposing a rule, palette or recipe

Use the **Rule or recipe proposal** template. Every rule in this repository
states two things, and a proposal should too:

- **the decision it turns on.** What does the author have to choose, and what
  are the options?
- **the failure it prevents.** What goes wrong without the rule? A before/after
  image is the strongest evidence.

Claims about a journal's specification (sizes, fonts, file formats) need a link
to the journal's published artwork guidelines. A judgement call is welcome as a
judgement call, but it should not be presented as a journal requirement.

Out of scope: code or data tied to one specific project, and styling that
contradicts a journal's published specification.

## Development setup

```bash
git clone https://github.com/Alto-R/nature-figure-craft.git
cd nature-figure-craft
python -m pip install -r requirements-dev.txt
python -m pytest
```

The test suite runs every module's self-test in a temporary directory, checks
that exported PDFs keep text as embedded TrueType, and exercises
`profile_data.py` on a fixed table.

The chord-diagram tests need R with `circlize`, and skip otherwise:

```r
install.packages("circlize")
```

CI also runs a lint pass for hard errors. To run it locally:

```bash
ruff check --select E9,F63,F7,F82 --target-version py39 .
```

## Conventions

- **Match the surrounding code.** Comments explain *why* a choice was made,
  not what the line does; the existing modules are the reference.
- **Every module keeps a self-test on synthetic data** (`if __name__ ==
  "__main__":` in Python, `if (sys.nframe() == 0L)` in R). No project data and
  no network access in self-tests or tests.
- **Sizes are landed sizes.** Type is specified by what it measures on the
  printed page (see `nature_style.panel()` and `references/spec.md`), never by
  a raw `figsize` or `cex`.
- **The PDF is the deliverable.** Exports must embed their fonts. Matplotlib
  needs `pdf.fonttype = 42`; R needs `cairo_pdf()`.
- **Python 3.9+.** CI tests 3.9 and 3.13.
- **The READMEs are bilingual.** A change to `README.md` needs the matching
  change to `README-EN.md`, and the other way round.
- **Add a test** when you fix a bug that a test could have caught.

## Pull requests

1. Fork, then branch from `main`.
2. Make the change, with tests where they apply.
3. Run `python -m pytest`.
4. Add a line under `## [Unreleased]` in `CHANGELOG.md`.
5. Open the pull request and fill in the template. CI must pass before merge.

## Licensing of contributions

By contributing, you agree that your contribution is licensed under the
repository's terms:

- **code** (`*.py`, `*.R`, tests, workflows) under the [MIT License](LICENSE);
- **documentation and skill content** (`*.md`, including `SKILL.md` and
  `references/`) under [CC BY 4.0](LICENSE-docs). Code samples inside the
  documentation may also be used under MIT.

New code files start with the SPDX header used throughout the repository.

## Releases

Versions follow [Semantic Versioning](https://semver.org/). While the version is
0.x, a minor release may change behaviour, and each such change is recorded in
`CHANGELOG.md`. To cut a release, the maintainer:

1. moves the `Unreleased` entries into a new `## [X.Y.Z] - YYYY-MM-DD` section,
   and adds its compare link at the bottom of the file;
2. tags the commit `vX.Y.Z` and pushes the tag.

The release workflow then publishes that version's changelog section as the
GitHub release notes. The README's release badge picks up the new version on
its own.
