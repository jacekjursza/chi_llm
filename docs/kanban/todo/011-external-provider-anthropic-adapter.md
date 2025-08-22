# External provider: Anthropic adapter (basic)

## Summary (What)
Add `AnthropicProvider` for `generate` and `chat` using official SDK.

## Why (Context)
- docs_tmp U-4 and U-5 (MAX users) require Anthropic support.

## Scope (How)
- Implement with API key + model in config.
- Return text; handle basic errors.

## Acceptance Criteria
- `provider.type=anthropic` works for generate/chat.
- Docs snippet with env var names.

## Dependencies
- 002 Provider schema.

## Risks
- Model naming differences; document defaults.

## Estimate
- Complexity: M (0.5 day)

## Test Plan
- Mocked SDK.

