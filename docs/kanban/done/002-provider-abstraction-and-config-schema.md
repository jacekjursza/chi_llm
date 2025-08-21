# Provider abstraction and config schema (Done)

## Summary (What)
Design and introduce a provider abstraction to support multiple backends (local llama.cpp, LM Studio, Ollama, external APIs). Extend config schema to include provider type and connection settings.

## Outcome
- Added minimal `Provider` protocol (`generate`, `chat`, `complete`).
- Extended config loader with `provider` section and env overrides.
- `MicroLLM` reads provider config; default behavior preserved.
- Docs updated with Provider Configuration (draft).
- Unit tests cover config parsing for provider fields.

## Notes
Implementations for non-local providers tracked in separate cards.

