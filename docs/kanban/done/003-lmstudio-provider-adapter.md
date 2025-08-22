Title: LM Studio provider adapter (Done)

Outcome:
- Implemented `LmStudioProvider` with OpenAI-compatible endpoints.
- MicroLLM routes `generate/chat/complete` to LM Studio when configured, skipping local model load.
- Added clear error messages for unreachable server.
- Updated docs with config examples; added unit tests.

Acceptance Criteria:
- `provider.type=lmstudio` triggers routing: met.
- Errors surfaced with actionable guidance: met.
- Minimal docs snippet added: met.

Notes:
- Streaming and model discovery tracked in separate cards.

