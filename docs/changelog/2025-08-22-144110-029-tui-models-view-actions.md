# TUI Models View Actions (029)

## Summary
- Added interactive actions in the Textual UI to manage models:
  - Set default model (local/global) via a simple modal prompt.
  - Download model via a modal prompt.
- Introduced a `ModelsController` that bridges TUI intents to the store.
- Enhanced models list with quick CLI fallback instructions.

## Context
This continues card 029 to make model discovery and selection effortless in the TUI, while keeping UI code thin and testable.

## Files
- `chi_llm/tui/views/models.py` — controller + formatting helpers.
- `chi_llm/tui/app.py` — modal screens and keybindings (`s`, `x`).
- `tests/test_tui_models_controller.py` — controller tests and formatting checks.

## Notes
- UI tests stay non-terminal by testing the controller/formatting; interactive screens are simple and optional.
- Download path remains offline-friendly; clear error surface on failure.

