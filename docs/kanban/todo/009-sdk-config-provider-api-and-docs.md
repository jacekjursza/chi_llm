# SDK: expose config provider API and docs

## Summary (What)
Document and stabilize a small API for using chi_llm as a configuration provider in external apps.

## Why (Context)
- docs_tmp U-6: reuse chi-llm’s configuration system elsewhere.
- We already have `ModelManager` and config loading; need a stable, documented surface.

## Scope (How)
- Add a `config` helper module (or document existing functions) with: `load_config()`, `resolve_model()`, `get_provider_settings()`.
- Ensure these are imported in `__init__` for stable access.
- Create `SDK_USAGE.md` section for config provider usage with examples.

## Acceptance Criteria
- Public functions stable and covered by basic tests.
- Documentation published and linked from README.

## Dependencies
- 002 Provider schema.

## Risks
- Backward compatibility; mark experimental if needed.

## Estimate
- Complexity: S (3–5h)

## Test Plan
- Unit tests for APIs returning expected shapes with various config sources.

