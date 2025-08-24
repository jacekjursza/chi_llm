package tui

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"strings"
)

// ProviderConfig holds configuration for a specific provider
type ProviderConfig struct {
	// Provider type
	Type string `json:"type"`

	// Server-based providers (lmstudio, ollama)
	Host string `json:"host,omitempty"`
	Port string `json:"port,omitempty"`

	// API providers (openai)
	APIKey  string `json:"api_key,omitempty"`
	BaseURL string `json:"base_url,omitempty"`
	OrgID   string `json:"org_id,omitempty"`

	// Common fields
	Model   string `json:"model,omitempty"`
	Timeout int    `json:"timeout,omitempty"`
}

// ConfiguredProvider represents a configured provider with tags
type ConfiguredProvider struct {
	ID     string         `json:"id"`     // unique identifier
	Name   string         `json:"name"`   // display name
	Type   string         `json:"type"`   // provider type
	Tags   []string       `json:"tags"`   // assigned tags
	Config ProviderConfig `json:"config"` // type-specific config
}

// MultiProviderConfig holds multiple configured providers
type MultiProviderConfig struct {
	Providers         []ConfiguredProvider `json:"providers"`
	DefaultProviderID string               `json:"default_provider_id,omitempty"`
}

// AvailableTags holds the list of available tags from chi_llm
type AvailableTags struct {
	Tags []string `json:"tags"`
}

// GetDefaultConfig returns default configuration for a provider type
func GetDefaultConfig(providerType string) ProviderConfig {
	config := ProviderConfig{Type: providerType}

	switch providerType {
	case "local":
		// Local provider doesn't need host/port

	case "lmstudio":
		config.Host = "localhost"
		config.Port = "1234"

	case "ollama":
		config.Host = "localhost"
		config.Port = "11434"

	case "openai":
		// API key will be set by user
		config.Model = "gpt-3.5-turbo"

	case "claude-cli", "openai-cli":
		// CLI providers don't need configuration
	}

	return config
}

// NeedsConfiguration returns true if the provider requires configuration
func NeedsConfiguration(providerType string) bool {
	switch providerType {
	case "lmstudio", "ollama", "openai":
		return true
	case "local", "claude-cli", "openai-cli":
		return false
	default:
		return false
	}
}

// GetConfigurableFields returns which fields can be configured for a provider
// schemaCache caches provider field schemas fetched from CLI.
var schemaCache map[string][]string

// GetConfigurableFields returns which fields can be configured for a provider.
// The schema is fetched from the chi-llm CLI (`providers schema --json`).
func GetConfigurableFields(providerType string) []string {
    if schemaCache == nil {
        schemaCache = map[string][]string{}
        type field struct{ Name string `json:"name"` }
        var payload struct{
            Providers []struct{
                Type   string  `json:"type"`
                Fields []field `json:"fields"`
            } `json:"providers"`
        }
        cmd := exec.Command("chi-llm", "providers", "schema", "--json")
        if out, err := cmd.Output(); err == nil {
            if json.Unmarshal(out, &payload) == nil {
                for _, p := range payload.Providers {
                    names := make([]string, 0, len(p.Fields))
                    for _, f := range p.Fields {
                        if f.Name != "" {
                            names = append(names, f.Name)
                        }
                    }
                    schemaCache[p.Type] = names
                }
            }
        }
    }
    if fields, ok := schemaCache[providerType]; ok && len(fields) > 0 {
        // Always append tags as a UI-level concept
        hasTags := false
        for _, f := range fields { if f == "tags" { hasTags = true; break } }
        if !hasTags { fields = append(fields, "tags") }
        return fields
    }
    // Fallback minimal
    if providerType == "local" { return []string{"model", "tags"} }
    return []string{"tags"}
}

// GetAvailableTags fetches available tags from chi_llm CLI
func GetAvailableTags() ([]string, error) {
	cmd := exec.Command("chi-llm", "providers", "tags", "--json")
	output, err := cmd.Output()
	if err != nil {
		// Return fallback tags if command fails
		return []string{
			"tiny", "small", "medium", "large",
			"fast", "balanced", "powerful",
			"coding", "reasoning", "thinking-mode",
			"cpu-friendly", "recommended", "default",
		}, nil
	}

	var result AvailableTags
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("failed to parse tags: %w", err)
	}

	return result.Tags, nil
}

// GenerateProviderID generates a unique ID for a provider
func GenerateProviderID(providerType string, name string) string {
	// Simple ID generation - could be enhanced with UUID
	if name != "" {
		safeName := strings.ReplaceAll(strings.ToLower(name), " ", "-")
		return fmt.Sprintf("%s-%s", providerType, safeName)
	}
	return fmt.Sprintf("%s-1", providerType)
}
