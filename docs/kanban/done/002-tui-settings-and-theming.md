# Settings and Theming (Language‑Agnostic)

Meta
- Type: Task
- Priority: P2
- Estimate: 0.5–1.0d
- Status: TODO
- See also: 001-tui-screens-keybindings-transitions-options.md (EPIC)

## Scope (How)
- Add Settings page for toggling theme/animation and persisting preferences.
- Theme tokens: harmonize focus/hover styles across views.
- Maintain fixed header height; avoid jitter during toggles.

## Acceptance Criteria
- `t` toggles theme globally; `a` toggles animation; both reflected in Settings.
- Focus/hover styles consistent across providers/models/diagnostics.
- Preferences persist during the session; file persistence optional.

## Notes
- Keep modules under 600 lines; incremental polish acceptable.
