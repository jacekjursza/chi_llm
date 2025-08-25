title: TUI — Providers dropdowns and enum fields

- Implemented dropdown overlay for provider “Type” and any schema field exposing `options`/`enum`/`choices`.
- Enter opens overlay; Up/Down navigates; Enter confirms; Esc cancels; respects theme.
- Special handling for model discovery:
  - `lmstudio` and `ollama`: runs `chi-llm providers discover-models` and shows results as dropdown.
  - `local-zeroconfig`: curated recommended models populate the `model` field options.
- Verified no regressions to Save/Test/Cancel flow and type selection.

Card-Id: 004
Refs: docs/kanban/done/004-tui-providers-dropdown-enum-fields.md
