Title: Go TUI migration kickoff – roadmap/cards updated, first parity slice

Summary
- We decided to migrate all TUI functionality from Python/Textual to a Go TUI (Bubble Tea/Bubbles/Lip Gloss) under `go-chi/`.
- Updated roadmap with a dedicated milestone, closed legacy Textual TUI cards, and added Go TUI parity TODOs.
- Implemented initial parity in Go TUI: Back navigation and project config write.

Changes
- Roadmap: add "Go TUI Parity" milestone and note Textual maintenance.
- Kanban:
  - Closed: 033/035/036 (superseded by Go TUI)
  - Added: 039 Config view parity, 040 Models management parity, 041 Providers model browser parity, 042 Bootstrap wizard, 043 Diagnostics parity
- Go TUI (`go-chi/`):
  - Keys: add `b` Back; Enter on Configure moves to (Re)Build; Enter on (Re)Build writes `.chi_llm.json` in CWD
  - Tests: add minimal tests for welcome title and config write
  - README: updated keys and migration note
- Docs: README/CLI updated to reference Go TUI as primary

Next
- Implement providers model browser and models management in Go TUI.
- Decide on global config write path and align Python config loader if needed.

