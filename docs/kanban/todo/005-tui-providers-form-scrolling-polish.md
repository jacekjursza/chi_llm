# Providers – Form scrolling and UI polish

Meta
- Type: Task
- Priority: P2
- Status: TODO

## Summary (What)
- Improve inline form scrolling and micro-polish UI elements (buttons alignment, spacing, messages, focus/hover styling).

## Why
- Large schemas can overflow the viewport; smoother scrolling and cues improve usability and clarity.

## Scope (How)
- Auto-scroll the visible window to keep the focused field centered when possible.
- Align Save/Cancel horizontally with consistent padding; ensure focus ring is clearly visible.
- Refine message line (truncate long text, prefix icons, stable colors).
- Minor spacing tweaks: uniform field height, consistent gaps between sections.

## Acceptance Criteria
- Moving focus (Up/Down/Tab) keeps the focused field in view without jumps.
- Save/Cancel alignment and focus styles are consistent across themes.
- No regressions to keyboard map or dropdown interactions.
