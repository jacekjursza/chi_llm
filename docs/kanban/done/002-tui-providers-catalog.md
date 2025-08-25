# Providers Catalog (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Status: Done

## Outcome
- Manage a backstage catalog of providers using schemas from CLI; dynamic form; save to `chi.tmp.json`.

## Scope
- List/add/edit/delete providers; inline dynamic form from `chi-llm providers schema --json`; tags field stored; test hook; model browser hook; save.

---
Done: 2025-08-25 — Implemented in `tui/chi-tui/src/providers.rs` (and modular state/view), including save and schema-driven form.
