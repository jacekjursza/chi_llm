# Rust/Ratatui Bootstrap (Language Decision Task)

Meta
- Type: Task
- Priority: P1
- Estimate: 1.0d
- Status: TODO
- See also: 001_screens_keybindings_transitions_options.md (EPIC), 002_navigation_keymap_skeleton.md

## Scope
- Initialize Rust project for the new TUI (binary crate): `cargo init --bin chi-tui` (name TBD).
- Dependencies (minimal): `ratatui`, `crossterm`; optionally `color-eyre` (error reports), `serde`/`serde_json` for CLI JSON, `tokio` (if async), `clap` (flags like `--no-alt`).
- App entry + screen loop skeleton compatible with task 002 (pages stubs, global keymap, help overlay, ESC semantics).
- CLI presence check: detect `chi-llm` on PATH; print install instructions and exit non-zero if missing.
- Cross-platform: Linux/macOS/Windows terminal support via `crossterm`.
- Build/run docs: `cargo run`, `cargo build --release`; note minimum Rust version (MSRV) if needed.

## Constraints
- Language/framework fixed: Rust + ratatui + crossterm; no UI business logic yet (002 handles behavior).
- Integration limited to invoking `chi-llm` subprocess (no direct Python API).

## Acceptance Criteria
- `cargo run` starts the TUI skeleton; shows Welcome; global keys route between pages; `?` toggles help; ESC/back works; q/Ctrl+C exit.
- Startup fails fast with a clear message when `chi-llm` not found (non-zero exit code).
- Code passes `cargo check`; compiles on Linux/macOS/Windows.

## Deliverables
- Rust crate in repo (under `tui/` or `apps/chi-tui/`, path do uzgodnienia), with README of build/run steps.
- Minimal CI hint (optional) and `.gitignore` for Rust target/artefacts.
