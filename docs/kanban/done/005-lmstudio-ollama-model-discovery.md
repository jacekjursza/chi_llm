Title: Discover installed models: LM Studio & Ollama (Done)

Outcome:
- Added provider discovery utilities to list models from LM Studio (`/v1/models`) and Ollama (`/api/tags`).
- SDK function `chi_llm.list_provider_models()` for programmatic access.
- `chi-llm models list` now shows a "Provider models" section (human-readable) when a provider is configured.
- Graceful fallback when provider is unavailable.

Acceptance Criteria:
- Returns list with id/name/size: met.
- CLI shows provider models when configured: met (human output; JSON unchanged).
- Fallback behavior implemented: met.

Notes:
- LM Studio endpoints may vary; discovery is best-effort.

