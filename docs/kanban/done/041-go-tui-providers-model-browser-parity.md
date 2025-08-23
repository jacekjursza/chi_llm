Title: Go TUI – Providers model browser parity — Done

Outcome
- Added a Model Browser page to Go TUI (key `m` on Configure) for LM Studio and Ollama.
- Lists models via HTTP discovery; selecting a model populates `provider.model`.
- Rebuild writes `.chi_llm.json` including `provider.type` and `provider.model`.

Details
- Discovery: `internal/discovery` with `LMStudioModels` (/v1/models) and `OllamaModels` (/api/tags).
- TUI: new page `PageModelBrowser`; help key `m`; view shows id and size (MB when available).
- Save: `WriteProjectConfig(type, model)` persists the choice.

Tests
- LM Studio: success + empty responses covered via `httptest`.
- Ollama: success path covered; size displayed when available.

