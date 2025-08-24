Title: Go TUI models: single source of truth via chi-llm CLI

Date: 2025-08-24

Changes:
- Discovery: Go TUI now reads the curated local models list from `chi-llm models list --json` (YAML-backed registry).
- Fallback preserved: if CLI is not available, a minimal placeholder list is used.
- CLI/SDK: YAML registry (`chi_llm/models.yaml`) introduced with `zero_config_default` and tuning fields (`n_gpu_layers`, `output_tokens`).
- Providers CLI: added `--model-path`, `--context-window`, `--n-gpu-layers`, `--output-tokens` for local provider.
- Docs: updated configuration and CLI usage.

Notes:
- Follow-ups tracked in Kanban 045 to surface downloaded/current indicators, tags, filters, and fitness badges in the TUI.

