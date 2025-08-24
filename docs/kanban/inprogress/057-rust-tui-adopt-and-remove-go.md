# 057: Adopt Rust TUI and Remove Go TUI

## Summary (What)
- Remove the legacy Go TUI (`go-chi/`) from the repository.
- Make Rust/ratatui UI (`tui/chi-tui/`) the sole, official interactive UI.
- Align CLI (`chi-llm ui`/`chi-llm config`) to build/run Rust TUI.
- Update roadmap and developer docs to reflect Rust TUI as source of truth.

## Why (Context)
- We standardized on Rust/ratatui for better DX, portability, and single UI codebase.
- Go TUI is retired and should no longer appear in repo or active plans.

## Scope (How)
- Delete `go-chi/` directory and any tracked binaries under it.
- Update `CLAUDE.md` to reference Rust TUI only; remove Go TUI sections.
- Update `docs/product/current/roadmap.md` from Go→Rust TUI milestones.
- Ensure README and docs/CLI.md already state Rust TUI (verify; adjust if needed).
- Keep `.gitignore` ignoring `go-chi/` and Rust `target/` directories.

## Acceptance Criteria
- `go-chi/` no longer present in repo (fully removed from version control).
- `chi-llm ui` launches/attempts to build Rust TUI; no Go fallback.
- Roadmap and CLAUDE.md show Rust TUI as primary; no guidance to use Go TUI.
- A concise changelog entry exists documenting the removal and new UI flow.
- Test suite remains green: `python -m pytest tests -v`.

## Notes
- Historical changelog entries mentioning Go TUI remain as history and need not be edited.
- If any Go TUI Kanban cards exist, mark them as retired in Done with a short note.
