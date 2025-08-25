title: TUI — Anthropic discovery + OpenAI/Anthropic model dropdown

- Added `providers discover-models --type anthropic` (uses x-api-key and anthropic-version headers).
- TUI probe now tests Anthropic and shows model count; Save gating treats Anthropic as tested when successful.
- Dynamic `model` dropdown added for OpenAI and Anthropic in Providers form (via CLI discovery).

Card-Id: 064
Refs: docs/kanban/done/064-tui-providers-anthropic-test-and-dropdown.md
