# Connectivity Test Utilities (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Estimate: 0.5–1.0d
- Status: TODO
- See also: 001_screens_keybindings_transitions_options.md (EPIC)

- Outcome: Shared utilities to test provider connectivity with timeouts and clear status messages.
- Constraints: Language/framework agnostic. Use simple HTTP requests where applicable; rely on CLI only when HTTP is unavailable.

## Scope
- LM Studio: probe `GET /v1/models` at configured host:port; capture HTTP status, latency, and parse model list length.
- Ollama: probe `GET /api/tags`; capture status, latency, and tags count.
- OpenAI‑compatible: `GET /v1/models` with `Authorization: Bearer <api_key>` and optional `OpenAI-Organization`; support custom `base_url`.
- Timeouts: per‑request timeout (e.g., 3–5s default) and overall guard; abort/update UI on timeout.
- Results: normalized result object `{ok: bool, status: int|None, latency_ms: int|None, message: str}` for UI consumption.
- Integration points: invoked from Providers (T action) and Diagnostics (optional check for active provider).

## Non‑Goals
- Authentication flows beyond API key header; retries/backoff beyond a single retry are out of scope.

## Acceptance Criteria
- Each probe handles connection errors/invalid hosts/SSL cleanly and returns `{ok: false, message}`.
- Success path populates latency and a brief summary (e.g., "LM Studio: 12 models").
- Timeouts do not freeze UI; user sees actionable message.

## Deliverables
- Language‑agnostic spec and interface for connectivity checks, ready to be called from screens.
