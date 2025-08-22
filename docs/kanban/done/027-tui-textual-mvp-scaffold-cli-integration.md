# TUI (Textual) MVP: Scaffold & CLI integration — Done

## Outcome
- Implemented Textual-based TUI MVP and made it the default for `chi-llm config`.
- Added `--legacy-node` flag to launch the existing Node/Ink UI.
- Optional extra `ui` with `textual>=0.58,<1` added to packaging.
- Clear hints when Textual or Node are missing.
- Tests cover both Textual path and legacy Node path.

## Files
- `chi_llm/tui/app.py` — minimal Textual App scaffold
- `chi_llm/cli_modules/ui.py` — CLI integration preferring Textual
- `pyproject.toml` — extras `[ui]`
- `tests/test_ui_cli.py` — updated tests

## Acceptance
- All acceptance criteria met; full test suite passing.

