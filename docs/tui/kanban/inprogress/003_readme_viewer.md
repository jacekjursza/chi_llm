# README Viewer (Language‑Agnostic)

Meta
- Type: Task
- Priority: P2
 - Estimate: 0.5d
 - Status: In Progress
- See also: 001_screens_keybindings_transitions_options.md (EPIC)

- Outcome: Scrollable Markdown viewer for project README with optional TOC sidebar.
- Constraints: Language/framework agnostic. Prefer rendering from local `README.md`; graceful fallback if missing.

## Scope
- Load and render `README.md` from project root; support headings hierarchy for TOC (H1–H3 sufficient).
- Scrolling: Up/Down, PgUp/PgDn. Toggle TOC with `h`. Global keys honored.
- Stable layout: TOC width fixed; toggling TOC does not shift content lines unpredictably.
- Basic inline formatting (bold/italic/code) and links (non-clickable ok); images skipped or shown as placeholders.

## Non‑Goals
- Full Markdown spec; external link opening.

## Acceptance Criteria
- File load errors are handled (message and return to Welcome with Esc).
- TOC toggle works; selection sync optional; no layout jitter when toggling.
- Rendering performance acceptable on typical README size (<20k chars).

## Deliverables
- README Viewer screen integrated with skeleton routing.
- Simple parsing utility for headings to build TOC entries.
