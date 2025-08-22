# TUI Diagnostics View & Report

## Summary (What)
Add a Textual diagnostics view surfacing environment checks, config sources, cache paths, provider readiness, with copyable/exportable report.

## Why (Context)
- Fast, actionable insights reduce setup friction and support load.

## Scope (How)
- `views/diagnostics.py` using existing diagnostics logic as a data source.
- Show: OS/Python, package versions, cache dirs, model stats, provider detections, Node presence (for legacy UI), errors.
- Actions: copy report to clipboard (if available) and export to file.
- Use store method `get_diagnostics()` returning a structured dict.

## Acceptance Criteria
- View renders a concise summary + details panel; copy/export works (export path shown).
- `get_diagnostics()` includes keys for versions, config_source, models_count, providers, and paths.
- Tests: shape of diagnostics dict; export path handling; safe behavior if clipboard unavailable.
- Pre-task API check: confirm diagnostics helpers and their outputs; align keys.

## Out of Scope
- Live streaming updates; deep provider introspection beyond simple pings.

## Dependencies
- Store (028); diagnostics helpers from `chi_llm/cli_modules/diagnostics.py` and models.

## Risks
- Platform differences; mitigate by focusing on robust, cross-platform checks and fallbacks.

## Test Plan
- Unit tests validating diagnostics dict and export logic; avoid terminal dependency.

