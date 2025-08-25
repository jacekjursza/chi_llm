# Providers Catalog (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Estimate: 1.5–2.0d
- Status: TODO
- See also: 001_screens_keybindings_transitions_options.md (EPIC)

- Outcome: Manage a backstage catalog of providers (add/edit/delete, tags, minimal validation) using schemas from CLI. Persist to `.chi_llm.tmp.json`.
- Constraints: Language/framework agnostic. Rely on `chi-llm providers schema --json` for field definitions and types. Do not hardcode provider taxonomy.

## Scope
- List configured providers from `.chi_llm.tmp.json` (create file if absent) + an "Add provider" item.
- Add provider flow: choose type from CLI-reported types; prefill defaults; start inline edit of fields.
- Edit fields inline using dynamic form built from CLI schema (type, required, default); Tab cycles fields; Enter confirms field; Esc cancels field.
- Manage tags (multi-select); Enter toggles; Esc leaves tag mode.
- Delete provider with confirmation.
- Save action (S): write the catalog to `.chi_llm.tmp.json` (pretty JSON). No activation implied.
- Hook: T (Test connection) triggers connectivity checks for network providers (see task 010) and shows status.
- Hook: m opens Model Browser (task 006) and writes selected model into provider config.

## Data Contract
- `.chi_llm.tmp.json` structure: `{ "providers": [ {"id": str, "name": str, "type": str, "tags": [str], "config": {...} } ], "default_provider_id"?: str }`
- Only provider catalog is managed here; default selection is separate.

## Acceptance Criteria
- CRUD works; saved file matches schema and includes only set fields.
- Minimal validation per type (e.g., OpenAI requires api_key before test).
- Esc priority on this page: tags > field edit > add mode > page back.

## Deliverables
- Providers screen integrated with skeleton routing and save/test/model hooks.
