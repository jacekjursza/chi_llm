# Docs & examples: providers and routing

## Summary (What)
Add comprehensive docs and examples for configuring providers, using tags/fallbacks, and bootstrap workflow.

## Why (Context)
- Ensure users can adopt new capabilities with confidence.

## Scope (How)
- Update README and `docs/configuration.md` with provider sections.
- Add examples under `examples/` for LM Studio, Ollama, OpenAI.
- Add troubleshooting section.

## Acceptance Criteria
- Docs sections present with runnable code samples.
- Examples pass in CI (where network-free via mocks).

## Dependencies
- Core provider features implemented.

## Risks
- Docs drift; keep concise and link to CLI help.

## Estimate
- Complexity: S (3–5h)

## Test Plan
- Lint docs; simple run of examples with mocked providers in CI.

