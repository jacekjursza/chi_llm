Title: Go-CHI TUI – next steps (mouse click, provider settings, save config, markdown, polish)

Context
- We migrated the UI to a Go Bubble Tea/Bubbles/Lip Gloss v2 setup and added a hero + split grid animation, sections (1 Welcome, 2 Configure Provider, 3 (re)Build configuration), mouse scroll, Bubbles Help, and overlay title/subtitle.
- This card tracks the next UX/functionality improvements to make the TUI more useful out-of-the-box.

Scope / Goals
- Add mouse click-to-select on provider list and rebuild options.
- Add an in-UI provider settings panel (host, port, model) and wire to existing config layer.
- Implement configuration save actions (project `.chi_llm.json` and global `~/.chi_llm.json`).
- Render Welcome with Markdown (Glamour) for nicer README excerpt.
- Small polish: animation contrast option, optional left padding for hero title/subtitle, minor help tweaks.

Non-Goals
- Full “crush” parity and advanced layering across all screens (can be a follow-up).
- Any provider network calls beyond basic validation (keep zero-config UX).

Implementation Notes
- Mouse: handle tea.MouseClickMsg; hit-test against list rows within the frame.
- Settings panel: simple form view toggled from Configure Provider (e.g., `s` key); fields persisted via project `.chi_llm.json` first; global path follow-up.
- Save actions: on (re)Build page, Enter triggers write to project `.chi_llm.json` (first); show success/error feedback.
- Markdown: use Glamour to render a limited slice of README; soft-wrap in a Viewport; fall back to plain text if Glamour unavailable.
- Polish: add a flag or key (e.g., `A`) to toggle stronger grid colors; optionally add 2-space left padding to hero overlay text.

Acceptance Criteria
- Mouse click on provider list changes selection; mouse click on rebuild options changes selection.
- Pressing `s` on Configure opens a lightweight settings panel; saving returns to list and updates in-memory config.
- On (re)Build, pressing Enter writes config to the selected scope and shows a confirmation line with path.
- Welcome section renders Markdown with headings and basic styling (when Glamour present); otherwise shows plain text.
- Help (`?`) includes new keys (e.g., `s`, any toggle for stronger grid).
- No regressions: resize keeps full-height frame; hero overlay title/subtitle remain left-aligned; animation still toggles with `a`.

How to Validate
- `chi-llm ui --go-rebuild` (interactive), verify mouse, sections, settings, and writes.
- `chi-llm ui --go-rebuild -- -no-alt` to sanity check snapshot output.

Risks
- v2 beta APIs may change; keep versions pinned and code paths small.

Done When
- All acceptance criteria pass on local testing; short note added to go-chi/README.md describing new interactions.
