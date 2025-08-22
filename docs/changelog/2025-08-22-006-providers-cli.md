# 006: Providers CLI

## Summary
- Added `chi-llm providers` with `list`, `current`, and `set` subcommands.
- JSON outputs for automation/UI; silent `set` for clean pipelines.
- Writes provider config under `provider` key to local/global config files.
- Docs updated with usage examples.

## Details
- New: `chi_llm/cli_modules/providers.py`
- CLI registry updated to include providers module
- Tests: `tests/test_providers_cli.py`
- Docs: `docs/CLI.md` (providers section)

Card-Id: 006
Refs: docs/kanban/done/006-providers-cli-commands.md
