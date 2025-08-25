title: Provider Protocol — add discover_models classmethod

- Extended `Provider` Protocol with optional `@classmethod discover_models(**kwargs) -> List[str]`.
- Implemented discovery on adapters:
  - `LmStudioProvider.discover_models(host, port)`
  - `OllamaProvider.discover_models(host, port)`
  - `OpenAIProvider.discover_models(api_key, base_url, org_id)`
  - `AnthropicProvider.discover_models(api_key, base_url)`
- Added `discover_models_for_provider(ptype, **kwargs)` helper in `chi_llm.providers` for unified access.
- Keeps existing CLI `providers discover-models` intact to not break tests/UI.

