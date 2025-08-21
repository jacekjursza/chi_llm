# Bootstrap command: project config and env placeholders (Done)

## Summary (What)
Add `chi-llm bootstrap .` to scaffold project configuration and helpful files.

## Outcome
- Generates `.chi_llm.json` (canonical project config; YAML via `--yaml`).
- Generates `.env.sample` with provider API key/host placeholders.
- Generates `llm-requirements.txt` with selected extras (none/standard/rag/rag-st/full).
- Non-interactive flags for CI; interactive prompts if flags omitted.

## Notes
- We standardized on JSON as canonical; YAML is optional for DX.
- External providers produce a `provider` section in config; local uses `default_model`.

