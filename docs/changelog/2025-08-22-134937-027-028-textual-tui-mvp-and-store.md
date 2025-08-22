# Textual TUI MVP (027) and Store Layer (028)

## Summary
- Switched `chi-llm config` to prefer a new Textual (Python) TUI by default.
- Kept legacy Node/Ink UI behind `--legacy-node`.
- Added a TUI store layer for atomic config reads/writes and model summaries.

## Details
- New `chi_llm/tui/app.py` bootstraps a minimal Textual app (Header/Footer/Home), imported at runtime only.
- `chi_llm/cli_modules/ui.py` now:
  - Detects Textual and launches it by default.
  - Offers `--legacy-node` to launch the previous UI.
  - Prints clear installation hints if Textual/Node are missing.
- Packaging: optional extra `ui` with `textual>=0.58,<1`.
- Store layer: `chi_llm/tui/store.py` provides `get_config`, `set_config` (atomic), `list_models`, `get_current_model`.
- Tests: `tests/test_ui_cli.py` updated; new `tests/test_tui_store.py` added; all tests pass.

## Rationale
- Reduce cross-platform friction by removing hard dependency on Node for config UI.
- Keep excellent UX path with Textual while providing a no-regression fallback.

## Notes
- Docs updates and Node UI deprecation messaging tracked in card 032.
