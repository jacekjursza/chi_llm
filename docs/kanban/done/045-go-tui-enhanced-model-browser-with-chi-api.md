# 045: Go TUI Enhanced Model Browser with Chi-LLM API Integration — Retired

Status: Retired (Go TUI removed in favor of Rust/ratatui)

Outcome:
- Work discontinued. The project adopted a Rust/ratatui TUI under `tui/chi-tui/`.
- Equivalent model browser capabilities will be implemented in Rust.

---

## Historical Goal
Enhance the Go TUI model browser to use rich data from `chi-llm models list --json` API, showing download status, resource requirements, tags, and intelligent filtering.

## Historical Progress
- [x] Go TUI calls `chi-llm models list --json` for local provider (single source of truth).
- [x] Show download status/current model indicators in UI.
- [x] Display detailed metadata (RAM, context window, tags).
- [x] Tag-based filtering (cycle with `f`).
- [x] Fitness indicators (fits RAM) with inline markers.
- [ ] Filter mode: Fits RAM only (pending)

## Notes
Migration path: implement model browser in `tui/chi-tui` with parity or better UX.
