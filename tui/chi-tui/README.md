# chi-tui (Rust/ratatui)

Terminal UI for chi-llm. This is a language-agnostic TUI implementation using Rust + ratatui + crossterm.

## Quickstart

- Requirements: Rust (stable), cargo

```
cd tui/chi-tui
cargo run -- --help
cargo run              # start in alt-screen
cargo run -- --no-alt  # start without switching to alternate screen
```

## Notes
- Checks for `chi-llm` in PATH on startup; prints an instruction and exits non-zero if missing.
- Global keymap: Up/Down, Enter, Esc, q/Ctrl+C, 1/2/3/4/b/s, `?` (help), `t` (theme), `a` (animation toggle).
- Pages scaffolded: Welcome, README, Configure, Select Default, Model Browser, Diagnostics, Build, Settings.
- Retro/Synthwave theme palette (neon magenta/cyan/blue) with dark background.

## License
MIT
