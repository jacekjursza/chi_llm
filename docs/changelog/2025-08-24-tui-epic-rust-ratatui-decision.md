# 2025-08-24 — TUI vNext EPIC, Rust/Ratatui Decision, Cleanup

Summary
- Defined TUI vNext EPIC and split into executable, language-agnostic tasks.
- Decided to implement the new TUI in Rust using ratatui.
- Removed legacy Go TUI from the repository; kept ignored locally.
- Cleaned temporary artifacts and aligned .gitignore.
- Created `devel` branch for ongoing TUI work.

Details
- EPIC: `docs/tui/kanban/todo/001_screens_keybindings_transitions_options.md` (now with decision note: Rust/ratatui).
- Tasks added: 002–010 under `docs/tui/kanban/todo/` with scope, acceptance, priorities, estimates.
- Moved 002 to In Progress: `docs/tui/kanban/inprogress/002_navigation_keymap_skeleton.md`.
- New task 011 (Rust bootstrap): `docs/tui/kanban/todo/011_rust-ratatui-bootstrap.md`.
- Cleanup: deleted `docs/*.png`, pytest output dumps, and dropped `go-chi/` from version control; added ignore rules.
- Branching: created and pushed `devel` tracking `origin/devel`.

References
- Card-Id: 001 (EPIC)
- Refs: `docs/tui/kanban/todo/001_screens_keybindings_transitions_options.md`
