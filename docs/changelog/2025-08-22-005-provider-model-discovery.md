# 005: Provider model discovery (LM Studio & Ollama)

## Summary
- Added discovery utilities for LM Studio and Ollama to list installed models.
- SDK function: `list_provider_models()`.
- `chi-llm models list` prints a "Provider models" section when a provider is configured.
- Graceful fallback on network/unavailable provider.

## Details
- New: `chi_llm/providers/discovery.py`
- SDK export in `chi_llm/__init__.py`
- CLI enhancement in `chi_llm/cli_modules/models.py`
- Tests: `tests/test_provider_discovery.py`

Card-Id: 005
Refs: docs/kanban/done/005-lmstudio-ollama-model-discovery.md
