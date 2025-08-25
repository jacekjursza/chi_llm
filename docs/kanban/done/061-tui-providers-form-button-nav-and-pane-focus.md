# 061 — TUI: Providers form left/right button nav + active pane focus (and README TOC focus)

Meta
- Type: UX improvement
- Status: Done
- Scope: Rust TUI (providers form, panel focus), README view (TOC)

## Summary
- Improve keyboard UX in Providers form and multi‑panel views:
  - Left/Right navigates between buttons in the form button group (Save/Cancel).
  - Up/Down navigates between form groups; buttons group acts as a single group.
  - Tab cycles focus between primary panels (list ↔ form). Shift+Tab cycles backward.
  - Visually highlight the active pane with a selected border color.
  - README view: with TOC visible, Tab switches focus TOC ↔ Content; Enter jumps to section.

## Acceptance Criteria
- Providers form: when focus is on buttons, Left/Right switches Save/Cancel; Up/Down moves between groups.
- Providers: Tab cycles focus between left list and right form; active panel is clearly highlighted.
- README: pressing `h` toggles TOC; with TOC visible, Tab switches focus TOC/Content; Enter jumps to section; active panel highlighted.
- Build succeeds; no regressions in Python test suite.

## Notes
- Footer/help updated to reflect new shortcuts.
- README documentation updated with shortcuts.

## Test Plan
- Manual: run `chi-llm ui`, navigate Configure, verify Left/Right on buttons; Tab cycles panels; borders highlight active.
- Manual: open README (1), toggle TOC (h), Tab to switch focus, Up/Down to move in TOC, Enter to jump.
- Automated: `python -m pytest tests -v` (all green as prior); `cd tui/chi-tui && cargo build`.

