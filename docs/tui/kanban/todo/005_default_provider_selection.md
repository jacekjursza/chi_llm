# Default Provider Selection (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Estimate: 0.5d
- Status: TODO
- See also: 001_screens_keybindings_transitions_options.md (EPIC)

- Outcome: Pick and persist the default provider from the backstage catalog to be used when building project config.
- Constraints: Language/framework agnostic. Operates on `chi.tmp.json` only.

## Scope
- List providers from `chi.tmp.json` with current default marked.
- Actions: Enter sets selected as default; S persists change to `chi.tmp.json`.
- Global keys honored; Esc returns to Welcome.

## Acceptance Criteria
- `default_provider_id` is created/updated in `chi.tmp.json` when selection changes.
- Selection is reflected on re-entry to the page.

## Deliverables
- Default Provider page integrated with skeleton routing.
