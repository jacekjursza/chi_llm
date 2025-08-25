# 2025-08-25 — TUI Settings and Theming (002)

## Summary
- Implemented a proper Settings page in the Rust TUI.
- Theme and animation toggles are visible and controllable from the UI.

## Details
- Added `tui/chi-tui/src/settings.rs` with `draw_settings` rendering.
- Wired Settings page into routing and key handling:
  - `t` toggles theme (Light/Dark), reflected immediately.
  - `a` toggles animations on/off.
  - On the Settings page: Up/Down to select an item, Enter to toggle.
- Kept consistent theming across views using shared `Theme` tokens.
- Preserved fixed header height to avoid layout jitter.

## Impact
- Users can now adjust theme and animation from the Settings page.
- No breaking changes to CLI or core Python package.

Card-Id: 002
Refs: docs/kanban/done/002-tui-settings-and-theming.md
