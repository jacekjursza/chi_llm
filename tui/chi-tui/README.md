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
- Global keymap: Up/Down, Enter, Esc, q/Ctrl+C, 1/2/3/4/b/s, `?` (help), `t` (theme), `a` (animation toggle), `l` (logs on Configure tests).
- Pages scaffolded: Welcome, README, Configure, Select Default, Model Browser, Diagnostics, Build, Settings.
- Retro/Synthwave theme palette (neon magenta/cyan/blue) with dark background.

### Status & Priorities

Status
- Bootable skeleton: Welcome, README (with TOC), Configure, Select Default, Model Browser, Diagnostics, Build, Settings.
- CLI integration: checks `chi-llm` presence; reads schemas (`providers schema`), diagnostics, model lists; runs provider tests and model discovery.
- Providers form: dynamic fields from schema, dropdowns for enum-like fields, model pickers per provider, connection Test gating before Save.
- Build: writes active provider to project (`.chi_llm.json`) or global cache; maps local variants to canonical `local`.
- UX: global keymap, help overlay, dark synthwave theme, basic settings (theme/animation).

Priorities (P0)
- E2E happy path: Configure → Test → Save → Set Default → Build (project/global) → `chi-llm models current --explain` matches selection.
- Error hardening: clear, actionable messages on CLI errors/timeouts; keep UI responsive.

Next (P1)
- Local-custom discovery: robust `.gguf` scan from `auto_discovery_gguf_paths` with empty‑state hints.
- Minor UX polish: consistent footers per page, subtle highlights, and focus states.
- Preferences: persist lightweight UI prefs (theme/alt-screen) between runs.

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
