title: Local providers — unified model discovery

- `discover_models_for_provider()` now supports `local`, `local-custom`, and `local-zeroconfig`.
  - `local` / `local-custom`: returns curated catalog IDs from `chi_llm.models.MODELS`.
  - `local-zeroconfig` (alias: `local-no-config`): returns recommended/default subset.
- CLI `providers discover-models` routes these types to the unified helper.
- Keeps TUI behavior intact (zeroconfig still reads options from schema), adds a consistent discovery path across the system.

