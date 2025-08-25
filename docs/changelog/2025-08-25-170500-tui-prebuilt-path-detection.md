# TUI: Prebuilt binary PATH detection in cli

- Added PATH-based detection and launch of a prebuilt `chi-tui` binary from `chi-llm ui`.
- Fallbacks remain:
  - If no binary on PATH, attempt to build and run the Rust TUI from `tui/chi-tui` when running inside the repo (Cargo required).
  - Otherwise, print clear instructions to obtain a prebuilt binary or build from source.
- README updated with shipping notes: using prebuilt binary on PATH vs building from source.

Context:
- Enables shipping the Rust/ratatui TUI as a standalone binary and smooth integration with the existing Python CLI without requiring the source tree.

