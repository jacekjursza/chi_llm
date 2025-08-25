# 2025-08-25 — Anthropic adapter and branch policy update

## Summary
- Add Anthropic provider adapter with Messages API support
- Integrate with ProviderRouter and MicroLLM core
- Expose CLI schema for `anthropic` (api_key + model)
- Update configuration docs with Anthropic section
- Add unit tests (fake SDK) — all tests green
- Update AGENTS.md: `devel` as working branch; `master` for integration/releases

## Context
- Enables external provider support beyond OpenAI/LM Studio/Ollama.
- Clarifies contribution flow and default push target during active development.

## Artifacts
- Card: 011 — docs/kanban/done/011-external-provider-anthropic-adapter.md
- Card: 060 — docs/kanban/inprogress/060-policy-branch-develop.md
- Commits:
  - feat(providers): add Anthropic adapter… (9d26c58)
  - docs(agents): update working branch policy… (37ee744)
