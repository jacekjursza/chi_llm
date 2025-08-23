Title: Go TUI – Providers model browser parity (041)

Summary
- Added model browser in Go TUI for LM Studio and Ollama (key `m` on Configure).
- Selecting a model sets `provider.model`; (Re)Build writes `.chi_llm.json` with provider type and model.

Technical
- New package: `go-chi/internal/discovery` for LM Studio `/v1/models` and Ollama `/api/tags`.
- TUI: `PageModelBrowser`, async discovery command, and list UI with size when available.
- Config write now accepts model: `WriteProjectConfig(type, model)`.

Tests
- LM Studio success + empty via `httptest`.
- Ollama success with size.

