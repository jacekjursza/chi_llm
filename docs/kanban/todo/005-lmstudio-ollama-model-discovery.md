# Discover installed models: LM Studio & Ollama

## Summary (What)
List locally available models from LM Studio and Ollama for selection in config/CLI.

## Why (Context)
- docs_tmp/vision-refined.md U-3.b: SDK to detect user-downloaded models.
- Enhances UX for provider selection.

## Scope (How)
- For LM Studio: call models listing endpoint (if available) or parse workspace metadata.
- For Ollama: use `/api/tags` endpoint to list models.
- Expose via SDK (`chi_llm.list_provider_models(provider=...)`).
- Integrate into CLI `chi-llm models list` when provider is set.

## Acceptance Criteria
- Function returns list with id/name/size for both providers.
- CLI path shows provider models when provider configured.
- Graceful fallback when provider not reachable.

## Dependencies
- 003/004 provider adapters.

## Risks
- LM Studio API differences across versions.

## Estimate
- Complexity: M (0.5 day)

## Test Plan
- Mock endpoints; verify parsing and CLI output formatting.

