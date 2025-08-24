# Changelog: Rust TUI adoption and Go TUI removal

Date: 2025-08-25

## Summary
- Removed the legacy Go TUI (`go-chi/`) from the repository.
- Adopted Rust/ratatui UI (`tui/chi-tui/`) as the sole interactive UI.
- Updated developer docs and roadmap to reflect Rust TUI.
- Kanban: retired remaining Go TUI cards and added a new Rust TUI adoption card (057).

## Details
- CLI `chi-llm ui` builds/launches the Rust TUI. Go fallback is disabled.
- `.gitignore` continues to ignore `go-chi/` and Rust `target/` artifacts.
- Roadmap updated: “Rust TUI Parity (ratatui)” milestone replaces Go-based plans.
- CLAUDE.md updated with Rust TUI dev commands and system notes.

## Acceptance
- `go-chi/` files removed from version control.
- `chi-llm ui` points to Rust TUI; no Go references.
- Tests remain green (run `python -m pytest tests -v`).

## Follow-ups
- Implement model browser, diagnostics, and bootstrap wizard in `tui/chi-tui` with parity or better UX.
- Add minimal Rust CI (fmt/clippy) and contributor notes.
