# OpenAI: Discover Models via CLI and Test Gating in TUI

Date: 2025-08-25
Card-Id: 063

## Summary
- Added OpenAI support to `providers discover-models` CLI.
- TUI Providers now uses this CLI for OpenAI model dropdown and for Test connection, enabling Save only after a successful test when changes are present.

## Technical
- `chi_llm/cli_modules/providers.py`: `discover-models` accepts `--base-url`, `--api-key`, `--org-id`; uses stdlib `urllib` to call `/v1/models`.
- `tui/chi-tui/src/providers/view.rs`: `probe_provider` routes to CLI for OpenAI and reports model count.
- `tui/chi-tui/src/main.rs`: dynamic model dropdown for OpenAI via CLI; test‑success gating updated to include OpenAI.

## Validation
- `python -m pytest` — all tests pass.
- `cargo build` for TUI — OK.

