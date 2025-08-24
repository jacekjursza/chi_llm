# Leftovers / Session Summary (TUI vNext)

This note captures context, status, and next steps from the current session.

## What We Did
- Planning & Kanban
  - Turned 001 into an EPIC and split into tasks 002–010.
  - Added 011 (Rust/ratatui bootstrap). Marked 003/004/005/006/007/008/011 as In Progress.
- Cleanup
  - Removed `go-chi/` from repo; added to `.gitignore` (kept locally).
  - Deleted temporary screenshots (`docs/*.png`) and pytest dumps; updated `.gitignore`.
  - Removed `coverage.xml` from repo.
- Branching
  - Created and pushed `devel` (active branch for new TUI work).
- Rust TUI (tui/chi-tui)
  - Bootstrap (ratatui + crossterm + clap + anyhow + serde/json).
  - Retro/synthwave theme; stable header; global keymap; help overlay.
  - Diagnostics (007): pulls `chi-llm diagnostics --json` and `models current --explain --json`; `e` export, `r` refresh.
  - Model Browser (006): `chi-llm models list --json`; filters `r` downloaded-only, `f` cycle tag, `i` info; Up/Down + Enter select; hands selected model back to Configure.
  - README Viewer (003): loads project `README.md`, simple heading styling, TOC toggle `h`, scrolling Up/Down/PgUp/PgDn.
  - Select Default (005): reads/writes `chi.tmp.json` (`default_provider_id`), Up/Down + Enter to set default.
  - Providers Catalog (004):
    - Lists providers from `chi.tmp.json` plus a “+ Add provider” row.
    - Add (A/Enter on +), Delete (D), Save (S) to `chi.tmp.json` (preserves `default_provider_id`).
    - Edit overlay for key fields: E model, H host, P port, K api_key, B base_url.
    - Connectivity tests (T): LM Studio `/v1/models`, Ollama `/api/tags`, OpenAI `/v1/models` with Bearer; 3s timeout.
    - Integration with Model Browser (`m`) to set `config.model`.
  - Build/Write Config (008): `g` toggles Project vs Global; Enter writes provider config to `.chi_llm.json` or `~/.cache/chi_llm/model_config.json` (only non-empty fields, pretty JSON, numeric ports preserved).
- CLI Integration
  - `chi-llm ui` launches the Rust TUI, auto-builds with cargo when stale; `--rebuild` forces a rebuild; arguments after `--` are passed to the TUI (e.g., `--no-alt`).
  - Documentation updated (README, docs/CLI.md) to reflect Rust/ratatui UI.

## Open Items / Next Steps
- 004 Providers Catalog
  - Inline dynamic forms based on `chi-llm providers schema --json` (Tab navigation, per-field validation, required fields hints).
  - Tags multi-select UI and persistence.
  - Optional: duplicate provider action; rename provider id/name.
- 006 Model Browser
  - Optional: Network sources (LM Studio, Ollama) in browser view (currently local CLI catalog).
  - Optional: “fitness vs RAM” indicator using diagnostics/explain output.
- 007 Diagnostics
  - Reuse shared connectivity utilities (see 010) for active provider test.
- 008 Build/Write
  - Post-write verification step (read-back and summarize), optional undo.
- 009 Settings & Theming
  - Persist theme/animation preference (project/global dotfile), token polishing.
  - Smooth transitions and minor visual polish.
- 010 Connectivity Utilities
  - Factor probing code into a shared module, unify status schema, add per-provider timeouts and nicer errors.
- 003 README Viewer
  - Optional: markdown features (code blocks, links), jump-to-TOC navigation and back.
- General
  - Refactor `tui/chi-tui/src/main.rs` (>600 lines) into modules (`screens/*`, `ui/theme.rs`, `cli.rs`, `net/probe.rs`).
  - Add minimal Rust CI/lint (fmt/clippy) and usage notes for contributors.
  - Verify Windows/macOS key handling; alt-screen `--no-alt` docs.

## Usage Notes
- Launch: `chi-llm ui` (auto-build) or `chi-llm ui --rebuild`.
- Keys (highlights):
  - Global: `?` help, `t` theme, `a` animation, digits for sections, `Esc` back, `q/Ctrl+C` quit.
  - Model Browser: `r` downloaded-only, `f` cycle tag, `i` info; Up/Down + Enter.
  - Configure: `A/Enter` add, `D` delete, `S` save, `m` model, `E/H/P/K/B` edit fields, `T` test.
  - Diagnostics: `e` export, `r` refresh.
  - Build: `g` target toggle, `Enter` write.

## Risks / Considerations
- OpenAI test requires a valid API key; handle 401/403 gracefully.
- Network timeouts and proxies (reqwest + rustls) — consider proxy env vars handling if needed.
- Ensure `.chi_llm.json` is minimal and backward-compatible (`llamacpp`→`local` mapping is respected by Python side).

## Branch & Locations
- Active branch: `devel`.
- TUI sources: `tui/chi-tui/`.
- UI launcher: `chi_llm/cli_modules/ui.py` (`chi-llm ui`).

