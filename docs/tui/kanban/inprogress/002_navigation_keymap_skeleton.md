# Navigation, Keymap & App Skeleton (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Estimate: 1.0d
- Status: In Progress
- See also: 001_screens_keybindings_transitions_options.md (EPIC)

- Outcome: Bootable TUI skeleton with global navigation, section routing, help overlay, ESC semantics, and CLI presence check. No business logic yet.
- Constraints: Language/framework agnostic. Integrate via `chi-llm` CLI outputs (JSON) and local files only. Go TUI is retired.

## Scope
- Bootstrap application shell with pages: Welcome, README, Configure, Select Default, Model Browser, Diagnostics, Build, Settings.
- Global keymap: Up/Down, Enter, Esc, q/Ctrl+C, digits 1/2/3/4/b/s, toggles `?` (help), `t` (theme), `a` (animation).
- Routing: section keys available from any page; Esc behavior consistent (page back; quit from Welcome when no modal active).
- CLI presence: On startup, detect `chi-llm` in PATH. If missing, display actionable message and exit non‑zero.
- Help overlay: compact legend of global keys; toggle with `?`.
- Layout contract: fixed header height when animation on; max‑width content container; no jitter during toggles.

## Non‑Goals
- Rendering README, provider CRUD, model lists, diagnostics, or file writes (handled in later tasks).

## Acceptance Criteria
- From Welcome, section shortcuts (1/2/3/4/b/s) navigate to the correct pages.
- Esc semantics: on any page goes one level back; on Welcome quits; q/Ctrl+C always quits.
- `?` shows/hides help overlay without layout jumps.
- Startup fails fast when `chi-llm` not found, printing install hint.
- Stable header height across toggles; screen resizes handled without misalignment.

## Deliverables
- Runnable TUI skeleton with stubs for all pages and global keymap routing.
- Minimal test/demo plan (manual): keystroke walkthrough proving navigation/quit/help.
