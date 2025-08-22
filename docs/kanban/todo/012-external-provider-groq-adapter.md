# External provider: Groq adapter (basic)

## Summary (What)
Add `GroqProvider` for `generate` and `chat` using Groq SDK or HTTP API.

## Why (Context)
- docs_tmp U-4 includes Groq.

## Scope (How)
- Implement with API key + model in config.
- MVP text outputs.

## Acceptance Criteria
- `provider.type=groq` works for generate/chat.

## Dependencies
- 002 Provider schema.

## Risks
- Rate limits; include timeouts.

## Estimate
- Complexity: M (0.5 day)

## Test Plan
- Mocked HTTP/SDK calls.

