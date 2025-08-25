# 065 — TUI: Scratch config unification and async test spinner

Meta
- Type: Task
- Priority: P0
- Status: Done

## Outcome
- Standardized scratch config filename to `.chi_llm.tmp.json` in Select Default and active docs.
- Provider connection tests run asynchronously with a 30s timeout and an ASCII spinner in UI.

## Scope
- Code: `tui/chi-tui/src/providers/select_default.rs`, `providers/state.rs`, `providers/view.rs`, `main.rs`, `util.rs`.
- Docs: updated TODO/In Progress references from `chi.tmp.json` to `.chi_llm.tmp.json` in relevant kanban and reference docs; historical Done cards left unchanged.

## Notes
- Spinner shows during test both under provider list (Status) and in form message; tests are non-overlapping and report results back to the form for save gating.
- Build verified: `cd tui/chi-tui && cargo build`.

## Acceptance
- Configure → Test shows spinner and completes within 30s (llamacpp-friendly).
- Select Default operates on `.chi_llm.tmp.json` consistently.

