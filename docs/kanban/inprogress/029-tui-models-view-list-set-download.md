# TUI Models View: list/set/download

## Summary (What)
Add a Textual view to browse available models, inspect details, set the default model, and manage downloads via `ModelManager`.

## Why (Context)
- Make model discovery and selection effortless; expose curated metadata and actions directly in TUI.

## Scope (How)
- `views/models.py` with:
  - Table/list of `MODELS` (filter by size/type; quick search).
  - Details panel: context window, RAM, file size, tags.
  - Actions: Set as default (local/global), mark/download using `ModelManager`.
  - Safe UX: confirm apply; inline errors.
- Use store layer for reads/writes; UI purely renders and dispatches intents.

## Acceptance Criteria
- User can set default model (local/global) and see success feedback.
- If not downloaded, trigger download path via store/manager (mocked in tests) and reflect state.
- Offline-friendly: clear message if download not possible here; suggest CLI fallback when needed.
- Tests: store interactions mocked; intent→store calls verified; no terminal-dependent tests for layout.
- Pre-task API check: confirm `ModelManager` methods for get/set/mark/download and model metadata shape.

## Out of Scope
- Actual network downloads in tests; streaming/async UI.

## Dependencies
- Store layer (028), `ModelManager`, `MODELS` registry.

## Risks
- Confusion around local vs global scope; mitigate with explicit labels and confirmations.

## Test Plan
- Unit tests on presenter/store bridging; ensure correct config writes and state updates.

