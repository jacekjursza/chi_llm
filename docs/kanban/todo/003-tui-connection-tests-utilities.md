# Connectivity Test Utilities (Language‑Agnostic)

Meta
- Type: Task
- Priority: P1
- Estimate: 0.5–1.0d
- Status: TODO
- See also: 001-tui-screens-keybindings-transitions-options.md (EPIC)

- Outcome: Shared utilities to test provider connectivity with timeouts and clear status messages.
- Constraints: Language/framework agnostic. Use simple HTTP requests where applicable; rely on CLI only when HTTP is unavailable.

## Scope
- LM Studio: probe `GET /v1/models` at configured host:port; capture HTTP status, latency, and parse model list length.
- Ollama: probe `GET /api/tags`; capture status, latency, and tags count.
- OpenAI‑compatible: `GET /v1/models` with `Authorization: Bearer <api_key>` and optional `OpenAI-Organization`; support custom `base_url`.
- Anthropic: `GET /v1/models` (or supported endpoint) with `x-api-key` and `anthropic-version` header; include concise errors.
- Timeouts: per‑request timeout (e.g., 3–5s default) and overall guard; abort/update UI on timeout.
- Results: normalized `{ok: bool, status: int|None, latency_ms: int|None, message: str}` for UI consumption.
- Integration points: invoked from Providers (T action) and Diagnostics (optional check for active provider).

## Acceptance Criteria
- Each probe handles connection errors/invalid hosts/SSL cleanly and returns `{ok: false, message}`.
- Success path populates latency and a brief summary (e.g., "LM Studio: 12 models").
- Timeouts do not freeze UI; user sees actionable message.
