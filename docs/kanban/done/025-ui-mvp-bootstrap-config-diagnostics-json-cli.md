# UI MVP: Bootstrap, Config editor, Diagnostics, JSON CLI

## Summary (What)
Deliver a minimal but polished Ink UI (chi-llm config) with Bootstrap flow, Config editor, and Diagnostics, plus CLI JSON outputs and safe config helpers for tight UI↔CLI integration.

## Why (Context)
- We now bundle a working UI shell; next step is real value: quick setup, clear config, and actionable diagnostics.
- JSON outputs in CLI let the UI stay deterministic and testable.

## Scope (How)
- UI Bootstrap:
  - Provider/model select → preview diff → write `.chi_llm.json` + `.env.sample`.
- UI Config:
  - Form for `temperature`, `max_tokens`, `preferred_context`.
  - Toggle JSON/YAML editor, inline validation, diff + save.
- UI Diagnostics:
  - Checks: Node/npm, Python, RAM vs model, cache dir, basic network.
  - Render results with fix hints (copyable commands).
- CLI extensions:
  - `chi-llm models info --json`, `chi-llm setup recommend --json`.
  - `chi-llm config get/set` for safe read/write (project/global).
- Packaging/DX:
  - Add MANIFEST.in to include `chi_llm/ui_frontend/**` in wheels.
  - Add `package-lock.json` for UI; prefer `npm ci` when lock present.
- Tests:
  - Python: JSON output tests; bootstrap golden-files.
  - UI: ink-testing-library snapshots for menu/models; mock CLI calls.

## Acceptance Criteria
- `chi-llm config` provides working Bootstrap and Config screens with diff preview and correct writes.
- Diagnostics screen shows pass/fail and suggested fixes.
- `models list/current/info --json` returns valid JSON.
- `config get/set` reads/writes project/global safely.
- UI assets included in wheel (pip install works end-to-end).

## Non-Goals
- Full provider implementations (LM Studio/Ollama) beyond selection UI.
- Advanced RAG UI (basic query/add can be future work).

## Dependencies
- Existing ModelManager, Bootstrap CLI.

## Risks
- Cross-platform npm behavior; mitigate with `--legacy-peer-deps` and lockfile.
- File write races; use atomic writes in config helpers.

## Estimate
- Complexity: M (2–3 days)

## Test Plan
- Unit tests for new CLI JSON outputs and config helpers.
- UI snapshot tests for core screens and flows.
- Manual E2E on Linux/macOS/Windows terminals.

