# 037: Go TUI (Bubble Tea) – provider select screen

## Goal
Create a proof-of-concept TUI in Go (Bubble Tea + Bubbles + Lip Gloss) under `go-chi/` with a single screen that lets the user select a provider: `llamacpp`, `lmstudio`, `ollama`.

## Scope
- New folder `go-chi/` with its own Go module.
- Minimal, ergonomic TUI with keyboard navigation and clear theming.
- Theming: light/dark toggle via a single key (e.g., `t`).
- Provider selection list (3 items) with visual focus and Enter to confirm.
- Minimal glue to print the chosen provider and exit gracefully.
- README with build/run instructions.
- Basic Go unit test (sanity, e.g., providers list content or theme toggle).

## Non-Goals
- Full integration with Python CLI.
- Network calls to providers.
- Complex routing/state management.

## Acceptance Criteria
- `go-chi` builds locally with `go build ./...`.
- Running `go run ./cmd/chi-tui` shows a single screen with a list of providers and supports Up/Down, Enter, `q`, and `t` for theme toggle.
- Selected provider is displayed/confirmed and the app exits cleanly.
- Theme visually changes (light vs. dark) and remains readable.
- README exists with quickstart instructions.
- At least one `*_test.go` test passes with `go test ./...`.

## Notes
- Favor small, focused files (<= 600 lines per file).
- Keep dependencies lean (Bubble Tea, Bubbles, Lip Gloss only).

