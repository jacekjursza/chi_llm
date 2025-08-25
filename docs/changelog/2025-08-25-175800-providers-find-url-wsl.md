# Providers: WSL-aware find-url and auto-url set

- New CLI: `chi-llm providers find-url --type {lmstudio|ollama}` probes common endpoints (including WSL nameserver IP) and returns a reachable URL.
- `providers set --auto-url` auto-detects host/port for lmstudio/ollama and writes config (local/global as selected).
- Rust TUI: Providers form gets shortcut `U` to run find-url and fill host/port (user can Save to persist).
- Docs updated in `docs/CLI.md` and README shortcuts.

Context: Frequent WSL2 ↔ Windows host setup where LM Studio/Ollama run on Windows. This improves DX by discovering the correct bridge IP without manual steps.
