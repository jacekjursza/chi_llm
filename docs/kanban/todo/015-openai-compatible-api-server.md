# OpenAI-compatible API server (optional)

## Summary (What)
Expose a lightweight HTTP server implementing a subset of OpenAI Chat Completions API to proxy configured providers.

## Why (Context)
- docs_tmp U-???? mentions an OpenAI-compatible API (low priority) to simplify integration.

## Scope (How)
- FastAPI/Flask server with `/v1/chat/completions`.
- Route to selected provider via `Provider` interface.
- Config via env; disabled by default.

## Acceptance Criteria
- Minimal happy path works locally with curl.
- Basic auth/token support optional.
- Docs describe limitations and mapping.

## Dependencies
- 002 Provider schema; at least one provider adapter.

## Risks
- Misuse as production server; add warning and rate limiting knobs.

## Estimate
- Complexity: L (1–2 days)

## Test Plan
- Unit tests for handler mapping; integration test with stub provider.

