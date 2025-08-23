# chi-llm Go TUI (Bubble Tea)

Minimal Go TUI using Bubble Tea + Bubbles + Lip Gloss.
We are migrating all TUI functionality here (replacing the legacy Python/Textual UI).
Current screens:
- 1 Welcome (README excerpt)
- 2 Configure Provider (pick: `llamacpp`, `lmstudio`, `ollama`)
- 3 (Re)Build Configuration (write project `.chi_llm.json`)

## Quickstart

- Requirements: Go 1.21+

```
cd go-chi
# initialize modules (first time only if needed)
# go mod tidy

# Run
go run ./cmd/chi-tui

# Build
go build ./...

# Test
go test ./...
```

## Keys
- Up/Down or k/j: move selection
- Enter: confirm selection
- b: back to Welcome (from Configure/Rebuild)
- m: on Configure, open model browser (LM Studio/Ollama)
- t: toggle light/dark theme
- a: toggle retro-wave animation (neon banner + grid)
- q, esc, ctrl+c: quit

## Notes
- Dependencies: `bubbletea`, `bubbles` (key), `lipgloss`.
- On (re)Build, Enter writes a minimal project config to `.chi_llm.json`.
  - If you picked a model in the browser, it's saved as `provider.model`.
