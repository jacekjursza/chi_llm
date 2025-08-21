# 025: UI JSON endpoints and config helpers

## Summary
- Added CLI JSON outputs for `models info` and `setup recommend` to support the Ink UI.
- Added `config get --json` and `config set <key> <value> [--scope local|global]` with atomic writes.
- Improved UI startup: prefer `npm ci` when `package-lock.json` exists; fallback to `npm install`.
- Included UI assets in distribution via `MANIFEST.in`.

## Context
Implements the first slice of card 025 (UI MVP: Bootstrap/Config/Diagnostics + JSON CLI) to enable deterministic UI↔CLI communication and safe config mutations.

## Notes
- Tests added for new flags and commands.
- No breaking changes to existing CLI UX.

## Files
- chi_llm/cli_modules/models.py
- chi_llm/cli_modules/ui.py
- tests/test_models_cli.py
- tests/test_config_cli.py
- MANIFEST.in
- docs/CLI.md

