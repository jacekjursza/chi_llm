# 063 — OpenAI: Discover Models via CLI and Test Gating in TUI

Meta
- Type: UX + Integration
- Status: Done
- Scope: CLI providers module, Rust TUI (Providers)

## Summary
- CLI: `chi-llm providers discover-models --type openai [--base-url] [--api-key] [--org-id] --json`
- TUI (Providers):
  - Dropdown modeli dla OpenAI korzysta z CLI discover-models.
  - "Test connection" działa dla OpenAI i odblokowuje Save po udanym teście (gating jak dla LM Studio/Ollama).

## Validation
- `python -m pytest` — green.
- `cd tui/chi-tui && cargo build` — OK.

