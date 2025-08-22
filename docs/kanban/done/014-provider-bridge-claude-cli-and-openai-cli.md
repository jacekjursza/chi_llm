# Provider bridge: Claude CLI and OpenAI CLI

## Summary (What)
Added optional providers that shell out to `claude` (Anthropic CLI) and
`openai` CLI tools. Enables using locally authenticated vendor CLIs as
providers for `generate`/`chat`/`complete`.

## Scope (How)
- New adapters: `ClaudeCLIProvider`, `OpenAICLIProvider`.
- Wiring in `MicroLLM` via `provider.type=claude-cli|openai-cli`.
- Providers CLI list updated to show new supported types.
- Unit tests with mocked subprocess and binary presence.

## Acceptance Criteria
- With the respective type set and CLI installed, `generate`/`chat` return text.
- If CLI missing, clear error is raised.
- Tests pass green.

## Notes
- Chat flattens history into a single prompt (MVP).
- Optional config keys: `binary`, `args`, `timeout`, `model`.

