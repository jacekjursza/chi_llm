# Ollama provider adapter (basic)

## Summary (What)
Add Ollama HTTP client provider supporting `generate` and `chat` using configured `host`/`port`.

## Why (Context)
- docs_tmp/vision-refined.md U-3 calls for first-class Ollama support.

## Scope (How)
- Implement `OllamaProvider` conforming to `Provider`.
- Config keys: `provider.type=ollama`, `host` (default `127.0.0.1`), `port` (default `11434`), `model`.
- Normalize API differences vs LM Studio.

## Acceptance Criteria
- With `provider.type=ollama`, `MicroLLM.generate/chat` route via Ollama.
- Clear error when Ollama daemon not running or model missing.
- Minimal docs snippet (usage + config example).

## Dependencies
- 002 Provider abstraction & config schema.

## Risks
- Diverse model names/variants; require explicit `model` in config.

## Estimate
- Complexity: M (0.5 day)

## Test Plan
- Mock HTTP tests for generate/chat endpoints and error paths.

