Title: Go TUI – Config view parity (Done)

Problem
- Migrate config view from Python Textual to Go and reach parity for basic provider selection and saving.

Delivered
- Back navigation to Welcome.
- Configure: select provider (local/lmstudio/ollama) without exiting.
- Rebuild: choose where to save; implemented local project save to `.chi_llm.json`.
- Confirmation messages on save; test for project write (`TestWriteProjectConfig`).

Notes
- Global save and multi-provider flows continue in follow-up cards.

