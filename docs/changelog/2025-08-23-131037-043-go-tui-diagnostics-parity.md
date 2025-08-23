Title: Go TUI – Diagnostics view parity

Summary
- Added a Diagnostics page to the Go TUI (Bubble Tea) with basic provider/config status and environment hints.
- Implemented JSON export to `chi_llm_diagnostics.json` via the `e` key.
- Updated README shortcuts.

Context
- Aligns Go TUI with Python/Textual diagnostics capabilities for local, offline flows.

Details
- New page switcher: `4` opens Diagnostics.
- Minimal env checks per provider (OpenAI key presence, Ollama binary, optional LM Studio base URL).
- Added unit tests for diagnostics collection and export.

Card-Id: 043
Refs: docs/kanban/inprogress/043-go-tui-diagnostics-parity.md

