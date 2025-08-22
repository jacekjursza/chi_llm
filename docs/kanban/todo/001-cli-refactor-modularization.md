# Refactor CLI into modular subcommands

## Summary
Reduce `chi_llm/cli.py` (673 lines) below 600 lines by extracting subcommands into dedicated modules while preserving current behavior and UX.

## Context
- Code quality rule: max file size 600 lines (see AGENTS.md).
- Maintain zero‑config UX and existing script entry points.

## Scope
- Extract major commands (generate, chat, complete, ask, analyze, extract, summarize, translate, classify, template, rag, setup, models, interactive) into submodules (e.g., `chi_llm/commands/`).
- Keep `chi_llm/cli.py` as a thin dispatcher/parser.
- Preserve flags, help text, and backward‑compatible aliases.

## Acceptance Criteria
- `chi_llm/cli.py` ≤ 600 lines.
- All existing tests pass without changes to their semantics.
- CLI flags and outputs remain backward compatible.
- New modules covered by unit tests where appropriate.

## Non‑Goals
- No new features or behavioral changes.
- No renaming of commands or flags.

## Risks
- Subtle parsing/behavior differences; import cycles.

## Estimation
- 1–2 days including test adjustments.

## Test Plan
- Run `python -m pytest tests -v`.
- Add focused tests for new command modules if gaps are found.

