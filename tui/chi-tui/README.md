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

### Status & Priorities

- Shipping over backlog: Some historic TUI TODOs may be stale. Prioritize shipping the working Rust TUI (core flows, save/build from `.chi_llm.tmp.json` to `.chi_llm.json`, provider E2E test) over non‑essential polish.

### Local providers UX

- `local` / `local-zeroconfig`:
  - Field `model` supports a dropdown (Enter) with curated catalog IDs.
  - Models auto-download on demand; download status does not block selection.
  - Use `providers discover-models --type local` for the same list via CLI.

- `local-custom`:
  - Field `model_path` supports a dropdown (Enter) with discovered `.gguf` files.
  - Discovery roots come from `auto_discovery_gguf_paths` in config (recursive scan).
  - If no files are discovered, a hint is shown; you can also type the path manually.
  - Use `providers discover-models --type local-custom` for the same list via CLI.

## License
MIT
