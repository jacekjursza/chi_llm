Title: Config Resolution — project-first default and global opt-in

Context:
- We want a deterministic, project-first configuration order with an option to
  prefer env-first in CI/12-factor setups. Global user config should be
  disabled by default to avoid "magical" cross-project effects.

Scope:
- Add `CHI_LLM_RESOLUTION_MODE` (project-first|env-first) — default project-first.
- Add `CHI_LLM_ALLOW_GLOBAL` (0/1) — default 0, when 1 enables global config.
- Update `ModelManager` to implement the new order and flags; allow peeking
  `allow_global`/`resolution_mode` from project files.
- Ensure env `CHI_LLM_MODEL` overrides and is respected even with provider
  fallback.
- Update docs/configuration.md accordingly.

Acceptance Criteria:
- `ModelManager` loads configs per the new precedence, with global disabled by
  default.
- `MicroLLM` resolves `default_model` respecting env and only uses
  `provider.model` as a fallback when no explicit default is set.
- Documentation describes the new order and flags.

