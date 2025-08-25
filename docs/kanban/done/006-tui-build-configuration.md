# Build/Write Configuration (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Status: Done

## Outcome
- Write a minimal `.chi_llm.json` for project or global path using selected default provider; include only non-empty fields.

## Scope
- Target (project/global); resolve default provider; pretty-print; preserve only present fields.

---
Done: 2025-08-25 — Implemented in `tui/chi-tui/src/build.rs` (write_active_config) and integrated in UI.
