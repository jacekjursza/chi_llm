# Model Browser (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Estimate: 1.0–1.5d
- Status: TODO
- See also: 001_screens_keybindings_transitions_options.md (EPIC)

- Outcome: Browse/select models for a provider. Primary source: CLI local catalog; optional network listings for LM Studio/Ollama.
- Constraints: Language/framework agnostic. Prefer `chi-llm models list --json`. Network discovery is best-effort.

## Scope
- For local catalog: run `chi-llm models list --json`; display id, name, size, tags, downloaded/current flags; filters: r (downloaded-only), f (cycle tag filter), i (toggle info line).
- For LM Studio: `GET /v1/models`; for Ollama: `GET /api/tags` (optional if HTTP access undesired in MVP).
- Selection (Enter) writes chosen model id into the calling provider’s config (in-memory) and returns to Providers page.
- Global keys honored; Esc returns to Providers without changes.
- Optional: compute “fitness” vs available RAM using `chi-llm models current --explain --json` fields.

## Acceptance Criteria
- Local catalog loads; filters work; selection returns to caller with model set.
- No index out-of-range when filtering; layout stable.

## Deliverables
- Model Browser integrated with Providers page via the `m` action.
