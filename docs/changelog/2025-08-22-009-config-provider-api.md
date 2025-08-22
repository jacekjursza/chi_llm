# 009 – SDK config provider API

## Summary
Expose a stable config helper API to let external apps reuse chi_llm configuration and model resolution.

## Changes
- Added `chi_llm/config.py` with:
  - `load_config()` – stable import path (wrapper)
  - `resolve_model()` – returns effective model id/path/context and source
  - `get_provider_settings()` – normalized provider settings (local/lmstudio/ollama)
- Exported new API via `chi_llm.__init__` for stable access.
- Added tests: `tests/test_config_api.py`.
- Updated `SDK_USAGE.md` with a new "Config Provider API (SDK)" section.
- Linked the section from `README.md`.

## Rationale
Documented and stabilized a minimal surface to integrate chi_llm config in other tools without pulling in heavy runtime logic.

## Notes
- Backward-compatible; no breaking changes.
- Coverage remains above threshold; all tests green.

Card-Id: 009
Refs: docs/kanban/done/009-sdk-config-provider-api-and-docs.md
