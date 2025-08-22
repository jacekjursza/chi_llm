# Architecture Principles

## Principles
- Simple interfaces: define minimal, clear contracts (e.g., `Provider` with `generate`/`chat`).
- Small modules: keep modules focused and files ≤ 600 lines.
- SRP and loose coupling: one responsibility per module; avoid cross-module knowledge.
- YAGNI: add abstractions only when needed; keep defaults simple.
- No heavy plugin frameworks: prefer small, explicit adapters and factories.

## Patterns
- Provider Adapter: one adapter per backend (local, LM Studio, Ollama, OpenAI, etc.).
- Thin Router (optional): config-driven selection by tags and linear fallback order.
- CLI as Facade: CLI parses args and delegates to core/providers; no business logic in CLI.

## Boundaries
- Core (`chi_llm/core.py`): orchestration; speaks only to interfaces.
- Providers (`chi_llm/providers/*`): concrete adapters; no dependency on CLI.
- CLI (`chi_llm/cli.py` + commands): argument parsing and user I/O; calls core.
- RAG/Setup: separate modules; avoid coupling with providers beyond interfaces.

## Testing
- Contract tests for the `Provider` interface using stubs/mocks.
- Unit tests for adapters (HTTP/SDK mocked; no network).
- Keep CLI tests focused on parsing and delegation.

## Extending
1. Implement new adapter in `providers/` conforming to the interface.
2. Wire selection via config/env (no breaking changes to defaults).
3. Add minimal docs and tests; keep examples runnable without network.
