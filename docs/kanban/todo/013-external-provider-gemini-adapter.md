# External provider: Gemini adapter (basic)

## Summary (What)
Add `GeminiProvider` for `generate` and `chat` using Google SDK.

## Why (Context)
- docs_tmp U-4 includes Gemini.

## Scope (How)
- Implement with API key + model in config.

## Acceptance Criteria
- `provider.type=gemini` works for generate/chat.

## Dependencies
- 002 Provider schema.

## Risks
- SDK surface differs (generative models API); keep minimal mapping.

## Estimate
- Complexity: M (0.5–1 day)

## Test Plan
- Mocked SDK.

