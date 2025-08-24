Title: Models YAML registry and local provider model_path (Done)

Summary
- Introduce YAML-backed models catalog with zero_config_default.
- Add local provider support for model_path, context_window, n_gpu_layers, output_tokens.
- Add CLI: models validate-yaml; include available_ram_gb in models current --json.
- Update docs (CLI/configuration) accordingly.

Acceptance
- `chi-llm models list --json` reflects YAML catalog.
- Local provider can load a direct GGUF file via model_path.
- Validation command reports errors/warnings/stats.
