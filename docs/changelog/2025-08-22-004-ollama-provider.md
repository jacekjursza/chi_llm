# 004: Ollama provider adapter

## Summary
- Added `OllamaProvider` (local HTTP client) without hard dependency on requests.
- `MicroLLM` routes to Ollama when `provider.type=ollama` is set via config/env.
- Clear errors when Ollama is unreachable, including base URL and run hint.
- Documentation updated with configuration and usage.
- Unit tests for generate/chat and connection errors.

## Details
- New: `chi_llm/providers/ollama.py`
- Core: provider initialization and routing in `chi_llm/core.py`.
- Tests: `tests/test_provider_ollama.py`.
- Docs: `docs/configuration.md` (Ollama section).

## Notes
- Streaming and model discovery are separate tasks.

Card-Id: 004
Refs: docs/kanban/done/004-ollama-provider-adapter.md
