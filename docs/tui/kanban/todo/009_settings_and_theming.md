# Settings & Theming (Language‑Agnostic)

Meta
- Type: Task
- Priority: P2
- Estimate: 0.5d
- Status: TODO
- See also: 001_screens_keybindings_transitions_options.md (EPIC)

- Outcome: Provide theme/animation toggles and a consistent visual system based on tokens. Persistence optional.
- Constraints: Language/framework agnostic. No external dependencies required.

## Scope
- Toggles: `t` for theme (light/dark), `a` for animation on/off (global).
- Theme tokens: Title, Subtitle, Body, Accent, Help, Frame, Selected, Panel; ensure contrast and readability.
- Header: fixed line count when animation enabled; no jitter across frames.
- Optional persistence of preferences (project or global small dotfile) with sensible defaults.

## Acceptance Criteria
- Toggling does not cause layout jumps; header height stable.
- Theme applies consistently across all pages/components.

## Deliverables
- Settings screen with toggles and tokenized theming applied app-wide.
