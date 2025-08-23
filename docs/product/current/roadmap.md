# chi_llm Roadmap (Current)

## Vision
- Zero‑configuration‑first local LLM library with powerful opt‑in integrations (LM Studio/Ollama/external providers), great DX, and clean configuration.

## Themes
- Core reliability and simplicity (model mgmt, config, CLI UX)
- Developer Experience (docs, examples, tooling, errors)
- Performance & UX (streaming, async, optional GPU)
- Knowledge features (RAG polish)
- Distribution & adoption (PyPI, docs site)
- Go TUI Migration (replace legacy Textual UI)

## Milestones
- M1: Packaging & Onboarding
  - Publish to PyPI, update README install paths
  - Curate examples and quickstarts
  - Acceptance: `pip install chi-llm` works; examples runnable
- M2: CLI Modularization (Quality)
  - Refactor `chi_llm/cli.py` to < 600 lines via submodules
  - Preserve flags/UX; keep tests green
  - Acceptance: file size limit met; tests pass
- M3: Streaming & Async
  - Token streaming, async API parity for `generate/chat`
  - Acceptance: streaming demo; async tests/examples
- M4: RAG v2 Polish
  - Simplified config, better sources, indexing ergonomics
  - Acceptance: example showing sources + persistent DB
- M5: Go TUI Parity (Bubble Tea)
  - Migrate TUI features from Textual to Go (Bubble Tea/Bubbles/Lip Gloss)
  - Screens: Welcome, Configure Provider (with model browser), Models (manage/download/remove), Diagnostics, (Re)Build/Save config
  - Acceptance: `go run ./go-chi/cmd/chi-tui` covers parity scenarios; minimal tests under `go-chi/internal/...`
- M6: TUI Bootstrap Wizard (Go)
  - In-app bootstrap flow to scaffold project config
  - Acceptance: guided wizard writes `.chi_llm.json/.yaml`, `.env.sample`, `llm-requirements.txt`
- M6: Providers (Optional)
  - LM Studio/Ollama detection + config; external providers behind unified API
  - Acceptance: smoke tests for each provider path

## Notes
- Keep zero‑config path working at all times.
- Prefer incremental, test‑backed changes; add unit tests per feature.
- Reference architecture principles: `docs/architecture-principles.md`.
 - Python Textual UI enters maintenance mode; all new TUI work targets `go-chi/`.
