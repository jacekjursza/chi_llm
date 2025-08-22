# TUI Providers View: configuration & connection tests — Done

## Outcome
- Added store methods: `get_provider`, `set_provider`, `test_connection`.
- Implemented Textual hotkey `p` to show provider status and connection test.
- Tests cover provider set/get (local/global) and connection test success/failure.

## Files
- `chi_llm/tui/store.py` (provider APIs added)
- `chi_llm/tui/app.py` (Providers view action)
- `tests/test_tui_store_providers.py`

## Acceptance
- Provider changes write atomically; in-memory config refreshed.
- Connection tests use discovery utils and report `ok` and `models_count`.
- Full test suite passing.

