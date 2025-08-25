# Providers: Test Connection Button, Save Gating, and CLI-based Models for LM Studio/Ollama

Date: 2025-08-25
Card-Id: 062

## Summary
- Added a "Test connection" button to the Providers form and dimmed Save when changes are present and not yet tested.
- Introduced `chi-llm providers discover-models` (CLI) for `lmstudio` and `ollama`.
- TUI uses the CLI discovery to populate the `model` field dropdown (LM Studio/Ollama) and to run connection tests (no direct HTTP in TUI).

## Technical
- Python: `chi_llm/cli_modules/providers.py` gains the `discover-models` subcommand (stdlib urllib; no new deps).
- Rust TUI:
  - `FormState` holds `initial_hash` and `last_test_ok_hash` to enforce Save gating.
  - Buttons extended to `[ Test ] [ Save ] [ Cancel ]`; Left/Right navigates within group.
  - `probe_provider()` now shells out to CLI discovery for lmstudio/ollama.

## Validation
- Tests pass: `python -m pytest` (138/138).
- TUI builds: `cd tui/chi-tui && cargo build`.

