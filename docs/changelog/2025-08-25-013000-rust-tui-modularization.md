# Changelog: Rust TUI modularization (split main.rs)

Date: 2025-08-25

## Summary
- Refactored `tui/chi-tui` into modules and reduced `main.rs` size.
- Behavior is unchanged; pages and keybindings remain the same.

## Details
- New modules: `app.rs`, `theme.rs`, `util.rs`, `diagnostics.rs`, `readme.rs`, `models.rs`, `providers.rs`, `build.rs`.
- `main.rs` orchestrates event loop, header/footer, and page routing.
- Validated with `cargo build`; Python tests remain green.

## Acceptance
- All Rust source files < 600 lines.
- `chi-llm ui` builds/launches Rust TUI.
