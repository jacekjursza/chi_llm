Title: Remove legacy Python/Textual UI

Context:
- Textual-based UI caused intermittent hangs in tests and is no longer part of
  the product direction (Go TUI is the only interactive UI).

Scope:
- Remove `chi_llm/tui/` (Textual app, views, store).
- Drop CLI fallback to Textual in `chi_llm/cli_modules/ui.py`; print Go TUI
  instructions when Go is not available.
- Delete Textual-related tests and capture script.
- Update docs (CLI, README, CLAUDE) and packaging extras (remove `ui`).

Acceptance Criteria:
- `chi-llm config` no longer attempts a Textual fallback and prints clear Go
  TUI instructions when needed.
- No code or tests import `chi_llm.tui`.
- Docs reflect Go TUI as the only interactive UI.

