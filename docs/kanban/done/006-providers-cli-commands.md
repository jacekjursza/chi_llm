Title: Providers CLI: list/current/set (Done)

Outcome:
- Added `chi-llm providers` with subcommands `list`, `current`, and `set`.
- JSON outputs supported for automation/UI.
- Writes provider config under `provider` key to local/global config.
- Integrated into CLI and documented.

Acceptance Criteria:
- Commands work locally and globally without breaking `models` flow: met.
- Config persisted per existing precedence rules: met.

Notes:
- Future work: model discovery (Card 005), external providers, streaming.

