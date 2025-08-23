package tui

import (
    "encoding/json"
    "os"
    "strings"
)

// projectConfig represents the minimal on-disk config schema we write from Go TUI.
type projectConfig struct {
    Provider map[string]any `json:"provider"`
}

// WriteProjectConfig writes .chi_llm.json to the current working directory
// with a minimal provider configuration: {"provider": {"type": provType}}
// It returns the written file path.
func WriteProjectConfig(provType string, model string) (string, error) {
    if provType == "" {
        provType = "llamacpp"
    }
    p := map[string]any{"type": provType}
    if strings.TrimSpace(model) != "" {
        p["model"] = model
    }
    cfg := projectConfig{Provider: p}
    data, err := json.MarshalIndent(cfg, "", "  ")
    if err != nil {
        return "", err
    }
    path := ".chi_llm.json"
    if err := os.WriteFile(path, data, 0o644); err != nil {
        return "", err
    }
    return path, nil
}
