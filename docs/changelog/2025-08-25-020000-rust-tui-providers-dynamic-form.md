# Changelog: Rust TUI — Providers dynamic form (059)

Date: 2025-08-25

## Summary
- Implemented schema-driven provider form in the Rust TUI.
- Pressing `F` on the Providers screen opens a dynamic form based on
  `chi-llm providers schema --json`.

## Details
- Reads provider field schemas (name, type, required, default, help) and
  renders a navigable form.
- Controls: Up/Down navigate, Enter toggles edit, Tab next field,
  `s` saves, Esc closes.
- Required fields are marked and highlighted when empty; defaults are
  prefilled when value is missing.
- Saving writes values back into the selected provider's `config` in
  `.chi_llm.tmp.json`. Casting is applied for `int` fields; other types remain
  strings (secrets are displayed masked).

## Acceptance
- Build compiles (`cd tui/chi-tui && cargo build --release`).
- Keybindings intact (quick-edit shortcuts E/H/P/K/B remain available).

## Follow-ups
- Additional validation (masking per-field, enum constraints) and better
  error reporting on save.
