Title: Multi-provider routing with tags and fallbacks (Done)

Outcome:
- Added router with tag-based selection and fallback across providers.
- Supports `provider_profiles` in config with `name`, `type`, `host`, `port`, `model`, `tags`, `priority`, `timeout`.
- `MicroLLM` uses router automatically when profiles are present; set `llm.tags` to influence selection.
- Fallback to next profile on error/timeout.

Acceptance Criteria:
- Routing via tags and priority: met.
- Fallback behavior on provider error: met.
- Documentation includes examples: met.

Notes:
- Streaming/async not included (future work).

