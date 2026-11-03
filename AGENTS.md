# Working on nature-figure-craft

This repository provides two research-figure skills for Claude Code and OpenAI
Codex. Both clients use the same skill instructions, references and plotting code.

## Layout

- `chart-type-chooser/`: chart selection, reference rules and `assets/profile_data.py`.
- `nature-figure-production/`: artwork instructions, reference guides and Python/R
  plotting modules in `assets/`.
- Each skill's `agents/openai.yaml`: Codex display metadata and default prompt.
- `tests/`: data-profile checks, plotting self-tests and PDF font checks.
- `README.md` / `README-EN.md`: matching Chinese / English documentation.

## Editing conventions

- Maintain one shared workflow for Claude Code and Codex. Keep client-specific
  installation and invocation details in the READMEs and Codex UI metadata in
  `agents/openai.yaml`.
- Resolve skill resources relative to their `SKILL.md`; generated figures belong
  in the user's project. Do not assume a specific home directory or shell.
- Preserve the distinction between choosing a chart and producing its artwork.
  Carry forward agreed data paths, claims, filters and encoding decisions.
- Keep skill frontmatter names equal to their directory names and descriptions
  within 1,024 characters. A Codex default prompt mentions its `$skill-name`.
- Update both READMEs together and add changes under `Unreleased` in `CHANGELOG.md`.
- Support Python 3.9+. Follow the existing SPDX headers for new code files.
- Use synthetic data in tests. Check exported PDFs and font embedding when changing
  artwork code. Distinguish journal requirements from house-style preferences.

## Validation

Install development dependencies with `python -m pip install -r requirements-dev.txt`.
Run the relevant checks from the repository root:

```bash
python -m pytest
ruff check --select E9,F63,F7,F82 --target-version py39 .
```

R chord tests require R, `circlize` and cairo support; they skip when unavailable.
Map rendering additionally needs `cartopy` / `geopandas`. For skill-only edits,
check YAML, resource paths and documented installation commands. Report which
checks ran and whether client behavior was tested in a live session.

See `CONTRIBUTING.md` for contribution and licensing details.
