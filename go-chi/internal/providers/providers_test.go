package providers

import "testing"

func TestListContents(t *testing.T) {
    got := List()
    want := []string{LlamaCPP, LMStudio, Ollama}
    if len(got) != len(want) {
        t.Fatalf("unexpected length: got %d want %d", len(got), len(want))
    }
    for i := range want {
        if got[i] != want[i] {
            t.Fatalf("unexpected value at %d: got %q want %q", i, got[i], want[i])
        }
    }
}

