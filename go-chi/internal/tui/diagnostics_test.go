package tui

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func writeTempProjectConfig(dir, prov, model string) error {
	prev, _ := os.Getwd()
	if err := os.Chdir(dir); err != nil {
		return err
	}
	defer os.Chdir(prev)
	_, err := WriteProjectConfig(prov, model)
	return err
}

func TestCollectDiagnosticsReadsProjectConfig(t *testing.T) {
	tmp := t.TempDir()
	if err := writeTempProjectConfig(tmp, "ollama", "llama3.2:latest"); err != nil {
		t.Fatal(err)
	}
	prev, _ := os.Getwd()
	t.Cleanup(func() { _ = os.Chdir(prev) })
	_ = os.Chdir(tmp)

	d := CollectDiagnostics()
	if d.ProviderType != "ollama" {
		t.Fatalf("expected provider 'ollama', got %q", d.ProviderType)
	}
	if d.ProviderModel != "llama3.2:latest" {
		t.Fatalf("expected model in diagnostics, got %q", d.ProviderModel)
	}
	if d.ConfigPath == "" {
		t.Fatalf("expected config path to be set")
	}
}

func TestExportDiagnosticsWritesFile(t *testing.T) {
	tmp := t.TempDir()
	prev, _ := os.Getwd()
	t.Cleanup(func() { _ = os.Chdir(prev) })
	_ = os.Chdir(tmp)

	d := Diagnostics{ProviderType: "openai"}
	path, err := ExportDiagnostics("", d)
	if err != nil {
		t.Fatalf("export failed: %v", err)
	}
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("expected file to exist: %v", err)
	}
	// sanity: read back and confirm provider
	b, err := os.ReadFile(filepath.Base(path))
	if err != nil {
		t.Fatal(err)
	}
	var got Diagnostics
	if err := json.Unmarshal(b, &got); err != nil {
		t.Fatal(err)
	}
	if got.ProviderType != "openai" {
		t.Fatalf("expected provider in exported file, got %q", got.ProviderType)
	}
}
