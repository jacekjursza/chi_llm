title: CLI — providers discover-models uses provider adapters

- Rewired `chi-llm providers discover-models` to call provider-level `discover_models` implementations via `chi_llm.providers.discover_models_for_provider`.
- Updated tests to stub the new entrypoint and assert argument passthrough.
- Keeps CLI flags stable; behavior unchanged from user perspective.

