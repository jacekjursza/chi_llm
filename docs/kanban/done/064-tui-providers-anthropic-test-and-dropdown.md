# TUI — Anthropic discovery and model dropdown

Meta
- Type: Feature
- Status: Done

## Summary
- Add CLI discovery for `anthropic` provider (`providers discover-models --type anthropic`).
- Extend TUI probe to test Anthropic connectivity and report model count.
- Enable dynamic `model` dropdown for `openai` and `anthropic` providers (pulls models via CLI).
- Include Anthropic in Test gating that enables Save after a successful check.

## Notes
- Requires `api_key` in provider config for Anthropic/OpenAI to discover models.
- Respects existing UI/keyboard patterns and theming.
