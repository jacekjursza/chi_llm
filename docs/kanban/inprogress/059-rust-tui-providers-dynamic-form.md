# 059: Rust TUI — Providers dynamic form from schema

## Summary (What)
- Use `chi-llm providers schema --json` to render provider-specific dynamic forms.
- Allow navigating fields, editing values, and saving back to `.chi_llm.tmp.json`.

## Why
- Reduce hardcoded field handling; align TUI with CLI schemas and validation.

## Scope (How)
- Parse schema into map type→fields (name, type, required, default, help).
- New form overlay on Providers screen (`F`):
  - Up/Down navigate fields, Enter toggle edit, Tab next, `s` save, Esc close.
  - Save casts `int` fields to numbers; strings/secrets remain strings.
- Keep existing quick-edit keys (E/H/P/K/B) for convenience.

## Acceptance Criteria
- Pressing `F` opens a form matching the selected provider type.
- Required fields marked; defaults prefilled when no value exists.
- Saving writes values back to the selected provider `config` in `.chi_llm.tmp.json`.
- Build compiles; no regressions in keybindings or other screens.

## Notes
- Further validation (e.g., required enforcement, masking secrets) can be added next.
