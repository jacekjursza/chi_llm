package tui

import (
	"go-chi/internal/providers"
	"go-chi/internal/theme"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestNewModelWelcomeTitle(t *testing.T) {
	m := NewModel(providers.List(), theme.Light, false)
	if got := m.headerTitle(); got != "chi-llm • welcome" {
		t.Fatalf("unexpected title: %q", got)
	}
}

func TestWriteProjectConfig(t *testing.T) {
	tmp := t.TempDir()
	prev, _ := os.Getwd()
	t.Cleanup(func() { _ = os.Chdir(prev) })
	_ = os.Chdir(tmp)

	p, err := WriteProjectConfig("ollama", "llama3.2:latest")
	if err != nil {
		t.Fatalf("write project config failed: %v", err)
	}
	if p != ".chi_llm.json" {
		t.Fatalf("unexpected path: %s", p)
	}
	full := filepath.Join(tmp, p)
	if _, err := os.Stat(full); err != nil {
		t.Fatalf("expected config file to exist: %v", err)
	}
	// Verify saved model exists in JSON
	b, err := os.ReadFile(full)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(b), "\"model\": \"llama3.2:latest\"") {
		t.Fatalf("expected model in config, got: %s", string(b))
	}
}
