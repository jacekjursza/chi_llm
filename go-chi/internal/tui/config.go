package tui

import (
    "encoding/json"
    "os"
    "path/filepath"
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
        provType = "local"
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

// ReadLocalConfig reads the current provider configuration from local .chi_llm.json
// Returns provider type and model, or empty strings if not configured
func ReadLocalConfig() (providerType string, model string) {
    // Try to read from current directory
    configPath := ".chi_llm.json"
    data, err := os.ReadFile(configPath)
    if err != nil {
        // Also try parent directories (up to 3 levels)
        cwd, _ := os.Getwd()
        for i := 0; i < 3; i++ {
            cwd = filepath.Dir(cwd)
            testPath := filepath.Join(cwd, ".chi_llm.json")
            if testData, err := os.ReadFile(testPath); err == nil {
                data = testData
                break
            }
        }
    }
    
    if len(data) == 0 {
        return "", ""
    }
    
    var cfg projectConfig
    if err := json.Unmarshal(data, &cfg); err != nil {
        return "", ""
    }
    
    if cfg.Provider != nil {
        if typeVal, ok := cfg.Provider["type"].(string); ok {
            providerType = typeVal
            // Map old llamacpp to new local name for compatibility
            if providerType == "llamacpp" {
                providerType = "local"
            }
        }
        if modelVal, ok := cfg.Provider["model"].(string); ok {
            model = modelVal
        }
    }
    
    // Also check for default_model at root level (Python TUI format)
    var rootCfg map[string]any
    if err := json.Unmarshal(data, &rootCfg); err == nil {
        if defModel, ok := rootCfg["default_model"].(string); ok && model == "" {
            model = defModel
        }
    }
    
    return providerType, model
}
