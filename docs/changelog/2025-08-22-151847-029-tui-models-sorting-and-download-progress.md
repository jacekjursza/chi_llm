# TUI Models: sorting and download feedback (029)

## Summary
- Added sorting toggle (`o`) cycling: `id → name → size → downloaded`.
- Added non-blocking download with inline feedback: shows "Downloading..." and updates message when complete; row refreshes with ✅.

## Files
- `chi_llm/tui/views/models.py` — sorting logic, keybinding, threaded download feedback.

## Notes
- Threaded background download uses `call_from_thread` to update UI.
- No network activity in tests; path remains exercised via controller tests.

