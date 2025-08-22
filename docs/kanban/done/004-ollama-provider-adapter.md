Title: Ollama provider adapter (Done)

Outcome:
- Implemented `OllamaProvider` with /api/generate and /api/chat endpoints.
- MicroLLM routes calls to Ollama when configured; local model load skipped.
- Actionable connection errors (base URL + hint to `ollama serve`).
- Added unit tests and docs configuration snippet.

Acceptance Criteria:
- Routing works via `provider.type=ollama`: met.
- Clear errors when server unavailable/model missing: met.
- Minimal docs snippet present: met.

Notes:
- Streaming and model discovery tracked separately.

