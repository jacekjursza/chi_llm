# External provider: OpenAI adapter (basic)

## Summary (What)
Add `OpenAIProvider` for `generate` and `chat` using official SDK, configurable via env/config.

## Why (Context)
- docs_tmp U-4: support external providers via classic interfaces; OpenAI first.

## Scope (How)
- Implement `OpenAIProvider` with model id, API key from env/config.
- Map to our provider interface; simple text outputs for MVP.
- Respect timeouts and basic error handling.

## Acceptance Criteria
- With `provider.type=openai`, `MicroLLM.generate/chat` return strings.
- Clear error on missing key; guidance in message.
- Minimal docs example.

## Dependencies
- 002 Provider schema.

## Risks
- SDK version drift; pin minimal compatible version in extras.

## Estimate
- Complexity: M (0.5 day)

## Test Plan
- Mocked SDK calls; no network in tests.

