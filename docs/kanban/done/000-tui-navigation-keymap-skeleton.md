# Navigation, Keymap & App Skeleton (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Estimate: 1.0d
- Status: Done
- See also: 001_tui-screens-keybindings-transitions-options.md (EPIC)

- Outcome: Bootable TUI skeleton with global navigation, section routing, help overlay, ESC semantics, and CLI presence check.
- Constraints: Language/framework agnostic. Integrate via `chi-llm` CLI outputs (JSON) and local files only.

## Scope
- Bootstrap application shell with pages: Welcome, README, Configure, Select Default, Model Browser, Diagnostics, Build, Settings.
- Global keymap: Up/Down, Enter, Esc, q/Ctrl+C, digits 1/2/3/4/b/s, toggles `?` (help), `t` (theme), `a` (animation).
- Routing: section keys available from any page; Esc behavior consistent (page back; quit from Welcome when no modal active).
- CLI presence: On startup, detect `chi-llm` in PATH. If missing, display actionable message and exit non‑zero.

## Acceptance
- Section shortcuts navigate pages; Esc semantics consistent; `?` toggles help; startup fails clearly when `chi-llm` missing.

---
Done: 2025-08-25 — Implemented in Rust TUI (`tui/chi-tui/`), wired in `main.rs` and `app.rs`.
