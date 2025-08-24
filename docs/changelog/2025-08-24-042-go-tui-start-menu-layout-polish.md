Title: 042 – Go TUI Start Menu and Layout Polish

Summary
- Added centered Start Menu overlay with gradient frame and thick side borders
- ESC is Back to Start Menu; README moved to its own scrollable view
- Added EXIT item to Start Menu
- Narrowed left panel to ~23% width for better balance
- Extended CHI-LLM logo with subtle fading edges
- Introduced a max-width (110 cols) centered container to avoid full-width stretch
- Stabilized Welcome/README scrolling and removed flicker

Files Changed (highlights)
- go-chi/internal/tui/model.go: Start Menu overlay, ESC/EXIT handling, layout & max-width container
- go-chi/internal/theme/theme.go: frame top padding tweak
- go-chi/internal/tui/anim.go: extended ASCII logo edges
- go-chi/cmd/chi-tui (rebuilt)

Validation
- Built with: `go build ./cmd/chi-tui`
- Verified scrolling on README, ESC behavior, centering and max-width on wide terminals

