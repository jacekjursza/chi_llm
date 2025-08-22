# 016 – Docs & examples: providers and routing

## Summary
Updated documentation and added runnable examples to demonstrate provider configuration (LM Studio, Ollama) and routing via profiles.

## Changes
- Added examples:
  - `examples/provider_lmstudio.py`
  - `examples/provider_ollama.py`
  - `examples/provider_router.py`
- CLI docs: noted routing via `provider_profiles` in `docs/CLI.md`.
- Verified existing `docs/configuration.md` covers provider and routing; no runtime changes.

## Notes
- Examples rely on local services (LM Studio / Ollama) when available.
- No network calls are executed during tests.

Card-Id: 016
Refs: docs/kanban/done/016-docs-examples-providers-and-routing.md
