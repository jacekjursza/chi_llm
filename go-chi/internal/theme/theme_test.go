package theme

import "testing"

// Sanity check: styles render without panicking and produce non-empty output.
func TestNewStylesRender(t *testing.T) {
	for _, mode := range []Mode{Light, Dark} {
		s := New(mode)
		out := s.Title.Render("X")
		if out == "" {
			t.Errorf("empty render for mode %v", mode)
		}
	}
}
