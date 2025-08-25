# TUI/CLI: Provider connectivity test (003)

- Added `chi-llm providers test` subcommand returning normalized JSON:
  `{ok, status, latency_ms, message}` for LM Studio, Ollama, OpenAI, Anthropic,
  and local providers.
- Integrated Rust TUI Providers screen to use the new CLI probe for the "Test" action.
  Save is gated on a successful probe when fields changed.
- Added unit tests for CLI probe covering local, local-custom, OpenAI (missing key),
  and fast-fail LM Studio scenarios.
- Updated `docs/CLI.md` with usage examples.

Refs: docs/kanban/done/003-tui-connection-tests-utilities.md
