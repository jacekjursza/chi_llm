package tui

import (
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "strings"
)

// projectConfig represents the minimal on-disk config schema we write from Go TUI.
type projectConfig struct {
    Provider map[string]any `json:"provider"`
}

// WriteProjectConfig writes .chi_llm.json to the current working directory
// with full provider configuration
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

// WriteProjectConfigFull writes .chi_llm.json with full provider configuration
func WriteProjectConfigFull(config ProviderConfig) (string, error) {
    p := map[string]any{"type": config.Type}
    
    // Add all non-empty fields
    if config.Host != "" {
        p["host"] = config.Host
    }
    if config.Port != "" {
        p["port"] = config.Port
    }
    if config.APIKey != "" {
        p["api_key"] = config.APIKey
    }
    if config.BaseURL != "" {
        p["base_url"] = config.BaseURL
    }
    if config.OrgID != "" {
        p["org_id"] = config.OrgID
    }
    if config.Model != "" {
        p["model"] = config.Model
    }
    if config.Timeout > 0 {
        p["timeout"] = config.Timeout
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

// ReadLocalConfigFull reads the full provider configuration from local .chi_llm.json
func ReadLocalConfigFull() ProviderConfig {
    config := ProviderConfig{}
    
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
        return config
    }
    
    var cfg projectConfig
    if err := json.Unmarshal(data, &cfg); err != nil {
        return config
    }
    
    if cfg.Provider != nil {
        // Parse all provider fields
        if typeVal, ok := cfg.Provider["type"].(string); ok {
            config.Type = typeVal
            // Map old llamacpp to new local name for compatibility
            if config.Type == "llamacpp" {
                config.Type = "local"
            }
        }
        if hostVal, ok := cfg.Provider["host"].(string); ok {
            config.Host = hostVal
        }
        if portVal, ok := cfg.Provider["port"].(string); ok {
            config.Port = portVal
        } else if portNum, ok := cfg.Provider["port"].(float64); ok {
            config.Port = fmt.Sprintf("%d", int(portNum))
        }
        if apiKeyVal, ok := cfg.Provider["api_key"].(string); ok {
            config.APIKey = apiKeyVal
        }
        if baseURLVal, ok := cfg.Provider["base_url"].(string); ok {
            config.BaseURL = baseURLVal
        }
        if orgIDVal, ok := cfg.Provider["org_id"].(string); ok {
            config.OrgID = orgIDVal
        }
        if modelVal, ok := cfg.Provider["model"].(string); ok {
            config.Model = modelVal
        }
        if timeoutVal, ok := cfg.Provider["timeout"].(float64); ok {
            config.Timeout = int(timeoutVal)
        }
    }
    
    return config
}

// WriteMultiProviderConfig writes multiple providers to chi.tmp.json
func WriteMultiProviderConfig(providers []ConfiguredProvider) (string, error) {
    config := MultiProviderConfig{Providers: providers}
    data, err := json.MarshalIndent(config, "", "  ")
    if err != nil {
        return "", err
    }
    path := "chi.tmp.json"
    if err := os.WriteFile(path, data, 0o644); err != nil {
        return "", err
    }
    return path, nil
}

// WriteMultiProviderConfigWithDefault writes providers and default provider ID to chi.tmp.json
func WriteMultiProviderConfigWithDefault(providers []ConfiguredProvider, defaultProviderID string) (string, error) {
    config := MultiProviderConfig{
        Providers:         providers,
        DefaultProviderID: defaultProviderID,
    }
    data, err := json.MarshalIndent(config, "", "  ")
    if err != nil {
        return "", err
    }
    path := "chi.tmp.json"
    if err := os.WriteFile(path, data, 0o644); err != nil {
        return "", err
    }
    return path, nil
}

// ReadMultiProviderConfig reads multiple providers from chi.tmp.json
func ReadMultiProviderConfig() ([]ConfiguredProvider, error) {
    data, err := os.ReadFile("chi.tmp.json")
    if err != nil {
        return []ConfiguredProvider{}, nil // Return empty if file doesn't exist
    }
    
    var config MultiProviderConfig
    if err := json.Unmarshal(data, &config); err != nil {
        return nil, fmt.Errorf("failed to parse chi.tmp.json: %w", err)
    }
    
    return config.Providers, nil
}

// ReadMultiProviderConfigWithDefault reads providers and default provider ID from chi.tmp.json
func ReadMultiProviderConfigWithDefault() ([]ConfiguredProvider, string, error) {
    data, err := os.ReadFile("chi.tmp.json")
    if err != nil {
        return []ConfiguredProvider{}, "", nil // Return empty if file doesn't exist
    }
    
    var config MultiProviderConfig
    if err := json.Unmarshal(data, &config); err != nil {
        return nil, "", fmt.Errorf("failed to parse chi.tmp.json: %w", err)
    }
    
    return config.Providers, config.DefaultProviderID, nil
}
