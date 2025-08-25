# Model Browser (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Status: Done

## Outcome
- Browse/select models from CLI catalog; filters: downloaded-only, tag; optional info panel.

## Scope
- `chi-llm models list --json`; show flags; selection writes model id into provider config and returns.

---
Done: 2025-08-25 — Implemented in `tui/chi-tui/src/models.rs` and integrated with Providers (key `m`).
