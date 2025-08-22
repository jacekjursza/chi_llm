# TUI Store Layer: config read/write + tests — Done

## Outcome
- Implemented `chi_llm/tui/store.py` with atomic config writes and helper APIs.
- Added unit tests for config read/write, type coercion, and model summaries.

## Files
- `chi_llm/tui/store.py`
- `tests/test_tui_store.py`

## Acceptance
- `get_config`, `set_config`, `list_models`, `get_current_model` available.
- Atomic write via temp file replace; in-memory state refreshes post-write.
- Full test suite passing.

