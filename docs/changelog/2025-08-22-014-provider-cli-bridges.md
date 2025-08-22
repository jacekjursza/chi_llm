# 2025-08-22 — Provider bridges: Claude CLI and OpenAI CLI

Changes
- feat(providers): add `ClaudeCLIProvider` and `OpenAICLIProvider` to invoke vendor CLIs via subprocess.
- feat(core): wire new providers in `MicroLLM` (`provider.type=claude-cli|openai-cli`).
- feat(cli): providers list now includes `claude-cli` and `openai-cli` as implemented.
- test: add `tests/test_provider_cli.py` covering happy paths and missing binaries.

Notes
- Chat is implemented by flattening history into a prompt (MVP behavior).
- If the CLI binary is missing, a helpful error is raised on first use.

