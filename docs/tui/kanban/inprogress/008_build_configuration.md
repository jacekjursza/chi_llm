# Build/Write Configuration (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Estimate: 0.5–1.0d
- Status: TODO
- See also: 001_screens_keybindings_transitions_options.md (EPIC)

- Outcome: Write a minimal, schema-compliant `.chi_llm.json` for the project (and optionally global) using selected default provider.
- Constraints: Language/framework agnostic. File I/O only; no downloads or inference.

## Scope
- Target selection: Project (CWD) vs Global (user config path). Show paths.
- Resolve active provider: use `default_provider_id` from `.chi_llm.tmp.json` or allow explicit override for this write only (optional).
- Serialize provider config: include only non-empty fields; pretty-print; port may be number or string.
- Compatibility: on read, map legacy `llamacpp` → `local`.
- Confirm after write and show file path.

## Acceptance Criteria
- Written JSON is valid and includes only present fields under `provider` key.
- Re-running shows current state correctly; does not duplicate fields.

## Deliverables
- Build/Write screen integrated with skeleton routing.
