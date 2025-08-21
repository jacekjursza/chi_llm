# UI: bundled frontend and config command (Done)

## Summary (What)
- Add `chi-llm config` to launch a bundled Ink UI from within this repo.
- Bundle minimal UI scaffold under `chi_llm/ui_frontend`.
- Provide JSON output in models CLI for UI integration.

## Outcome
- `chi-llm config` installs dependencies on first run and launches the UI.
- UI shows a basic menu (Bootstrap, Models, Config) and allows setting the default model locally via the Models screen.
- `chi-llm models list --json` and `chi-llm models current --json` output machine-readable data.

## Notes
- UI is intentionally minimal; next steps: full Bootstrap flow, Config editor, Diagnostics, and Providers.
