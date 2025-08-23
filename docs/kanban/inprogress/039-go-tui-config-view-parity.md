Title: Go TUI – Config view parity (In Progress)

Problem
- We are migrating TUI from Python Textual to Go. The Config view needs parity for basic provider selection and saving.

Scope
- Add Back navigation to return to Welcome.
- Configure: select provider (llamacpp/lmstudio/ollama) without exiting.
- Rebuild: choose where to save; implement local project save to `.chi_llm.json`.
- Print a concise confirmation (path) on exit.

Acceptance Criteria
- Pressing `b` on Configure/Rebuild returns to Welcome.
- On Configure, Enter selects provider and navigates to Rebuild (no exit).
- On Rebuild, Enter writes `.chi_llm.json` in CWD with `{ "provider": { "type": "..." } }` and exits.
- `go test ./go-chi/...` includes a small test that exercises the flow in a temp dir.

Notes
- Global save path tracked as follow-up; Python currently loads provider only from project file or explicit env.
- Keep files <= 600 LoC; small helper for writing JSON.

