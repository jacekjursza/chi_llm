# Diagnostics (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Status: Done

## Outcome
- Present environment/configuration snapshot and allow exporting diagnostics JSON.

## Scope
- Use `chi-llm diagnostics --json` and `models current --explain --json`; export JSON; graceful degradation.

---
Done: 2025-08-25 — Implemented in `tui/chi-tui/src/diagnostics.rs`.
