# 046: Go TUI Provider Model Discovery Integration (Done)

## Summary
Integrated external provider model discovery (LMStudio/Ollama) into Go TUI. The model browser shows provider-specific models when editing server providers. Local provider uses `chi-llm models list --json` for the curated catalog.

## What was implemented
- LMStudio `/v1/models` and Ollama `/api/tags` HTTP discovery in Go (`internal/discovery`).
- TUI integration: when editing a provider and opening the model browser, it discovers and lists models from that provider.
- Error handling and loading states; fallbacks for local when CLI is not available.

## Acceptance
- Provider-specific models appear in the model browser.
- Sizes rendered when available (parameter size or MB).
- Manual refresh by reopening the browser.

