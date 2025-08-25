# TUI UX: Active pane focus, button group nav, README TOC focus

Date: 2025-08-25
Card-Id: 061

## Summary
- Providers form: Left/Right switches between `[ Save ]` and `[ Cancel ]`. Up/Down moves between form groups; buttons are a single group.
- Pane focus: `Tab` cycles focus between left (list) and right (form) panels; active pane has highlighted border.
- README view: when TOC visible (`h`), `Tab` switches focus TOC ↔ Content; `Enter` jumps to selected section. Active panel highlighted.
- Footer/help and README shortcuts updated.

## Context
- Improves keyboard ergonomics and focus clarity in multi-panel views.
- Aligns with expected UX where horizontal keys switch within horizontal button groups.

## Affected Files
- `tui/chi-tui/src/main.rs`: key handling (Providers, README), footer/help text.
- `tui/chi-tui/src/providers/view.rs`: active pane border highlighting.
- `tui/chi-tui/src/readme.rs`: TOC state, focus, and drawing.
- `README.md`: shortcuts section updated.

## Validation
- `python -m pytest tests -v` — no regressions (previously 138/138 pass).
- `cd tui/chi-tui && cargo build` — OK.

