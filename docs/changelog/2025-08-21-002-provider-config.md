# 2025-08-21 — Provider abstraction & config schema (foundation)

- Added minimal `Provider` protocol under `chi_llm/providers` (generate/chat/complete).
- Extended configuration loader to support `provider` section and env overrides:
  - `CHI_LLM_PROVIDER_TYPE`, `CHI_LLM_PROVIDER_MODEL`, `CHI_LLM_PROVIDER_HOST`,
    `CHI_LLM_PROVIDER_PORT`, `CHI_LLM_PROVIDER_API_KEY`.
- Updated `MicroLLM` to read provider settings without changing default behavior;
  if `provider.type` is `local` and a `model` is provided, it is used when
  `model_id` is not passed explicitly.
- Documentation: added Provider Configuration draft to `docs/configuration.md`.
- Tests: added coverage for provider config via file and env in `tests/test_utils.py`.

Refs: docs/kanban/inprogress/002-provider-abstraction-and-config-schema.md
