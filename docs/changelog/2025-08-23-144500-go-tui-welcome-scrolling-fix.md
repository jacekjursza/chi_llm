# Fix: Go TUI Welcome Screen Scrolling and Content Truncation

## Problems Fixed
1. The Welcome screen in the Go TUI was not scrolling vertically despite having content that exceeded the viewport height
2. README content was truncated at line 200, cutting off in the middle of documentation

## Root Causes
1. **Scrolling issue**: The viewport content was only being set once when empty (`if m.vp.GetContent() == ""`) in the View() function. This meant that after initial render, the viewport had no content to scroll through.
2. **Truncation issue**: The `loadWelcome()` function was limiting content to first 200 lines with `lines[:200]`, which truncated README.md (571 lines) at "# Ask specific questions" (line 198).

## Solutions
1. Changed the View() function to always set viewport content: `m.vp.SetContent(m.welcome)` instead of conditional setting
2. Added content setting in `ensureWelcomeViewportSize()` to handle viewport resizing scenarios
3. Removed the 200-line truncation limit - now loads full README.md content

## Files Modified
- `go-chi/internal/tui/model.go`: 
  - Fixed viewport content setting in View() and ensureWelcomeViewportSize()
  - Removed 200-line truncation in loadWelcome()

## Testing
- Built successfully with `go build ./cmd/chi-tui`
- All tests pass with `go test ./...`
- Full README.md content (571 lines) now loads and scrolls properly
- Scrolling works with arrow keys, PgUp/PgDn, and mouse wheel on the Welcome screen

## Impact
Users can now:
- Properly scroll through the entire Welcome screen content using keyboard navigation and mouse wheel
- Read the complete README.md documentation without truncation