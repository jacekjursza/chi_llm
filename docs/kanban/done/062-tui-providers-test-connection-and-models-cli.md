# 062 — TUI: Providers “Test connection” button + Save gating; LM Studio/Ollama models via CLI

Meta
- Type: UX + Integration
- Status: Done
- Scope: Rust TUI (Providers), CLI providers module

## Summary
- Added a “Test connection” button to Providers form alongside Save/Cancel.
- Save is disabled (dimmed) when form has unsaved changes and the current values were not successfully tested.
- Implemented provider-side model discovery via CLI: `chi-llm providers discover-models` for `lmstudio` and `ollama`.
- TUI uses CLI discovery to populate a dynamic dropdown for the `model` field for LM Studio/Ollama.
- Providers “Test connection” uses the CLI discovery under the hood (no direct HTTP in TUI).

## Acceptance Criteria
- Providers form renders buttons: [ Test ] [ Save ] [ Cancel ].
- Left/Right navigates between these buttons; Up/Down navigates groups.
- Save remains disabled until a successful Test is run after changes.
- On model field (LM Studio/Ollama), Enter opens a dropdown with models obtained via CLI discovery.

## Implementation Notes
- CLI: added `providers discover-models` in `chi_llm/cli_modules/providers.py` using stdlib `urllib`.
- TUI: `probe_provider()` calls the CLI; gating implemented with `initial_hash` and `last_test_ok_hash` on the form.

## Validation
- `python -m pytest tests -v` — green.
- `cd tui/chi-tui && cargo build` — OK.

