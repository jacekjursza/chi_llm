# TUI Models: scope selection and default marker (029)

## Summary
- Added scope selection (Local/Global) when setting default model within the Models view.
- Added a star marker (★) next to the current default model in the list.
- Details panel now shows whether the selected model is default.

## Files
- `chi_llm/tui/views/models.py` — star in list rows, scope modal, details update.

## Notes
- List re-renders after setting default to reflect the new star.
- Download action updates the row to show the checkmark without a full refresh.

