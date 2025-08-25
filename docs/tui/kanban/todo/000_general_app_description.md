# General App Description (Technology‑Agnostic)

Meta
- Type: Brief/Contract
- Scope: All UIs (framework/language agnostic)
- Stability: Stable (living document)
- Status: Reference
- See also: 001_screens_keybindings_transitions_options.md (EPIC)

- Context: Terminal UI that helps users configure and operate chi‑llm with local and remote LLM providers. This document defines the product behavior and technical scope independent of UI framework or language.
- Audience: CLI/TUI users, developers integrating chi‑llm into local projects, and maintainers.
- Outcome: A clear, framework‑neutral contract for pages, flows, data formats, and external integrations.

## Product Source of Truth
- chi‑llm: a Python toolkit and CLI for configuring and using local/remote LLM providers. It defines the canonical configuration schema (`.chi_llm.json`), provider taxonomy, model catalog (exposed via CLI), provider types and their field schemas, and operational commands (including downloads).
- TUI: a graphical‑text wrapper over chi‑llm. It does not reimplement core logic, registries, or business rules. Instead, it reads from and writes to chi‑llm contracts (files/CLI), delegating provider/model knowledge and downloads to chi‑llm.
- Principle: when there is a discrepancy, chi‑llm (CLI/JSON outputs) is authoritative. The TUI adapts to the CLI’s schemas and responses.

## Vision & Goals
- Provide an intuitive terminal UI to:
  - Read an overview (README) and navigate documentation.
  - Manage multiple providers (local engines, HTTP services, API providers) and select a default.
  - Browse available models (local catalog or remote listings) and choose one.
  - Validate connectivity and environment for quick diagnosis.
  - Write a minimal, correct project configuration file.
 - Keep dependencies minimal and avoid mandatory online services for core flows.

## Non‑Goals
- Orchestrating model downloads or background jobs.
- Implementing inference/chat inside the TUI.
- Complex plugin frameworks; prefer simple, explicit adapters.

## Users & Primary Use Cases
- Maker/Developer setting up a local project: select provider/model, write `.chi_llm.json`, confirm readiness.
- Advanced user with multiple providers: manage multiple entries, set a default, quickly verify connection.
- New user exploring docs: read README with TOC, understand capabilities and next steps.

## High‑Level Pages (Product)
- Welcome/Home: start menu with primary actions; compact animated header (optional); stable header height.
- README Viewer: markdown rendering in a scrollable viewport; optional TOC sidebar built from headings.
- Configure Providers: add/edit/delete providers; fields vary by provider type; tag assignment; validation; connection test.
- Select Default Provider: pick the default from configured providers.
- Model Browser: list models for selected provider (local via CLI catalog; HTTP for network services); filters and details.
- Diagnostics: snapshot of environment and project configuration; export as JSON.
- Build Configuration: write `.chi_llm.json` to project (and optionally a global config).
- Settings: basic preferences (e.g., theme/animation) for future extension.

## Navigation & Inputs (Default Mapping)
- Navigation: Up/Down (move), Enter (select), Esc (back), q/Ctrl+C (quit).
- Sections: 1 README, 2 Configure, 3 Select Default, 4 Diagnostics, b Build, s Settings.
- Configure: A/a add, S save, D delete, T test connection, m open model browser, Tab next field.
- Model Browser: r downloaded‑only (local), f cycle tag filter (local), i info line.
- Help: ? toggles help/legend (optional), a toggles animation, t toggles theme.

## Data Contracts
- Project Config `.chi_llm.json` (minimal, only non‑empty fields):
  - `{"provider": {"type": str, "host"?: str, "port"?: str|int, "api_key"?: str, "base_url"?: str, "org_id"?: str, "model"?: str, "timeout"?: int}}`
  - Compatibility: map legacy `llamacpp` to `local` on read.
- Scratch Multi‑Provider `.chi_llm.tmp.json`:
  - `{ "providers": [ {"id": str, "name": str, "type": str, "tags": [str], "config": {...} } ], "default_provider_id"?: str }`
- Local Models Catalog (via CLI): list of entries including `id`, `name`, `size`(string), `file_size_mb`(int), `context_window`(int), `recommended_ram_gb`(float), `tags`([str]), `downloaded`(bool), `current`(bool).

## External Integrations (Source of Truth)
- CLI (required): `chi-llm` provides local models catalog (`models list --json`), available RAM (`models current --explain --json`), tags (`providers tags --json`), provider types and configurable fields (`providers schema --json`, or equivalent), and performs downloads.
- HTTP endpoints for discovery/connectivity:
  - LM Studio: `GET /v1/models` (base URL configurable).
  - Ollama: `GET /api/tags`.
  - OpenAI: `GET /v1/models` with `Authorization: Bearer` (optional `OpenAI-Organization`).
- Behavior: retry/timeouts as appropriate; show concise status. The TUI requires `chi-llm` CLI to be present; if missing, TUI informs the user and exits.

### Technology Baseline
- chi‑llm implementation language: Python.
- TUI implementation: unconstrained (Go, Python, Rust, etc.).
- Integration anchor: CLI and JSON files to keep the TUI portable across languages and frameworks; optional direct Python API use is allowed when the TUI is also in Python, but the source‑of‑truth remains the CLI/JSON contracts.

## Compatibility & Environment
- Platforms: Linux, macOS, Windows (modern terminals). Minimum viewport ~80×24; prefers ANSI-capable terminals.
- Alt-screen: optional; provide a flag to disable (e.g., `--no-alt`) for terminals where it’s undesirable.
- Offline-first: all core flows (readme, configure, build, diagnostics) work offline; network used only for discovery/connectivity checks.
- CLI presence (hard requirement): detect `chi-llm` on PATH at startup. If missing, display a clear instruction to install `chi-llm` and exit.

## Versioning & Contracts
- CLI contracts are authoritative: provider list, field schemas per provider, tags, and models are fetched from the CLI. Tolerate unknown fields; default missing fields; do not rely on undocumented keys. If a capability is missing, extend the CLI rather than hardcoding in TUI.
- JSON read/write: pretty-printed, stable field names; ports may be string or number; legacy `llamacpp` mapped to `local` on read.
- Backward compatibility: avoid breaking UI flows when CLI adds fields; treat additions as non-breaking.

## State Model & Event Loop (Conceptual)
- Single application state (page, dimensions, theme tokens, keymap flags, animation on/off, provider list, form inputs, model list, statuses).
- Event loop processes input events (keys/mouse), timers (animation), window resize, and async task completions (model discovery, connection tests).
- Async tasks return messages with payloads and errors; UI updates are idempotent and cancel‑safe.

## Layout & Theming (Conceptual)
- Max‑width content container (e.g., 110 cols), centered; ANSI‑aware width/padding to avoid misalignment.
- Header has fixed line count when animation enabled: grid top (1), hero (3), grid bottom (1), spacer (1).
- Theme tokens: Title, Subtitle, Body, Accent, Help, Frame, Selected, Panel.
- Optional left panel/TOC ~23% width (20..45 cols) separated by ` │ `; stable width across frames.

## Provider Configuration (Functional)
- Provider types: `local`, `lmstudio`, `ollama`, `openai`, `claude-cli`, `openai-cli`.
- Fields by type:
  - local: model, tags.
  - lmstudio/ollama: host, port, model, tags.
  - openai: api_key, model, base_url, org_id, tags.
  - cli types: tags.
- Actions: add (prefill defaults), edit (inline inputs), delete, save (write scratch config). Validation: minimal per type (e.g., OpenAI requires API key). Tags selectable from available tag list.
- Semantics: configuring one or many providers does not make them active; this creates a backstage catalog. The active provider is chosen separately.
- Default provider: selectable and persisted in scratch; used as the primary candidate when building/writing the project config.
 - Provider list and configurable fields are fetched from the CLI; TUI does not hardcode provider taxonomy or schemas.

## Model Browser (Functional)
- Sources:
  - Local (CLI catalog; required): rich metadata; show downloaded/current markers; compute suitability vs available RAM; filters: downloaded‑only, tag.
  - Network (HTTP): list IDs/sizes when available.
- Selection sets provider’s model and returns to configuration.

## Diagnostics (Functional)
- Read `.chi_llm.json` (CWD up traversal permissible) to determine provider and model.
- Collect environment hints per provider (e.g., presence of API key env var; binary in PATH).
- Export diagnostics JSON to a file; UI shows saved path.

## Build/Write Configuration (Functional)
- Write `.chi_llm.json` to project directory (and optionally a global path if selected).
- Resolve the active provider from the default selection (or an explicit choice at write time).
- Include only non‑empty fields; pretty‑print; handle numeric or string port; preserve existing where appropriate.

## Provider Selection Semantics
- Multi-provider configuration is a catalog; it does not imply activation.
- Tags: used to classify providers and enable filtering/recommendations in the UI (e.g., "coding", "fast", "recommended"). Tags do not activate a provider by themselves.
- Default provider: represents the preferred choice; when writing the project config or resolving the active provider, the default is used. If future flows include tag-constrained selection, the default acts as the tie‑breaker within the filtered set.

## Performance & UX
- No layout jitter during animation; constant header height on animated screens.
- Async operations must be cancellable and time‑bounded.
- UI responsive during IO and network calls (non‑blocking updates).

## Accessibility & Usability
- Full keyboard control; clear focus states; color contrast suitable for dark/light terminals.
- Status lines concise; errors actionable.

## Security & Privacy
- Do not log sensitive values (API keys). Store keys only in user config when explicitly provided.
- Network calls restricted to discovery/connectivity checks; no telemetry by default.
 - Mask secrets in UI; show only last 4 chars where necessary. Provide clear guidance where to place secrets (env vars vs config).

## Error Handling & Feedback
- Status line: concise, actionable messages for success/failure; avoid walls of text.
- Banners: short‑lived success/failure banners for save/export operations.
- Diagnostics: route complex failures to Diagnostics export when helpful.
- Never crash on CLI/network errors; always present a degraded but usable state.

## Acceptance Criteria
- All listed pages render and navigate per keymap.
- Provider CRUD + save work with validation and persist to scratch config; default provider selection persisted.
- Model discovery works (CLI/HTTP) with filters and selection; graceful fallback when unavailable.
- Diagnostics summarize environment and export JSON without network calls.
- Build writes a minimal, correct `.chi_llm.json`.
- Layout stable; theme tokens applied consistently; ANSI width/padding correct.

## Open Questions
- Persist UI preferences (theme/animation) to a user settings file?
- Should multi‑provider scratch become a stable config? If so, where?
- Include optional import/migration from legacy configs?
