# 003: LM Studio provider adapter

## Summary
- Added `LmStudioProvider` (OpenAI-compatible HTTP client) with no hard dependency on external libs (uses `requests` if available, falls back to `urllib`).
- MicroLLM now routes `generate/chat/complete` to LM Studio when `provider.type=lmstudio` is set via config or environment.
- Clear, actionable error messages when LM Studio server is not reachable.
- Docs updated with LM Studio configuration and usage snippet.
- Unit tests added for happy path and connection errors.

## Details
- New: `chi_llm/providers/lmstudio.py`
- Core: conditional provider init and routing in `chi_llm/core.py` (skips local model load when external provider configured).
- Tests: `tests/test_provider_lmstudio.py` (3 tests) + sanity check file.
- Docs: `docs/configuration.md` updated (LM Studio section).

## Notes
- Defaults: host `127.0.0.1`, port `1234`; requires enabling LM Studio local server.
- Streaming and model enumeration are out of scope (tracked separately).

Card-Id: 003
Refs: docs/kanban/done/003-lmstudio-provider-adapter.md
