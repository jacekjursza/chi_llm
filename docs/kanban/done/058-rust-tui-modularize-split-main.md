# 058: Rust TUI — Modularize and split main.rs (Done)

## Summary
- Split `tui/chi-tui/src/main.rs` into modules: `app.rs`, `theme.rs`, `util.rs`, `diagnostics.rs`, `readme.rs`, `models.rs`, `providers.rs`, `build.rs`.
- Rewrote `main.rs` to orchestrate pages, draw header/footer, and handle keys.

## Acceptance
- `cargo build` succeeds; TUI launches via `chi-llm ui`.
- No behavior regression (same pages and keybindings).
- Each file < 600 lines (checked by inspection).
- Python test suite remains green.

## Notes
- Next: add `cargo fmt`/`clippy` CI, and continue feature work per 057.
