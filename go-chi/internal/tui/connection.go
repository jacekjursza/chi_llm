package tui

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// ConnectionStatus represents the result of a connection test
type ConnectionStatus struct {
	Success   bool
	Message   string
	Details   string
	Latency   time.Duration
}

// TestConnection tests connectivity to a provider based on its configuration
func TestConnection(config ProviderConfig) ConnectionStatus {
	switch config.Type {
	case "lmstudio":
		return testLMStudio(config)
	case "ollama":
		return testOllama(config)
	case "openai":
		return testOpenAI(config)
	case "local", "claude-cli", "openai-cli":
		return ConnectionStatus{
			Success: true,
			Message: "Provider doesn't require connection testing",
		}
	default:
		return ConnectionStatus{
			Success: false,
			Message: "Unknown provider type",
		}
	}
}

// testLMStudio tests connection to LM Studio server
func testLMStudio(config ProviderConfig) ConnectionStatus {
	host := config.Host
	if host == "" {
		host = "localhost"
	}
	port := config.Port
	if port == "" {
		port = "1234"
	}
	
	url := fmt.Sprintf("http://%s:%s/v1/models", host, port)
	start := time.Now()
	
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Get(url)
	latency := time.Since(start)
	
	if err != nil {
		return ConnectionStatus{
			Success: false,
			Message: "Connection failed",
			Details: err.Error(),
			Latency: latency,
		}
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != 200 {
		return ConnectionStatus{
			Success: false,
			Message: fmt.Sprintf("HTTP %d", resp.StatusCode),
			Details: "LM Studio server returned error",
			Latency: latency,
		}
	}
	
	// Try to parse JSON response to verify it's a valid LM Studio endpoint
	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return ConnectionStatus{
			Success: false,
			Message: "Invalid response",
			Details: "Server response is not valid JSON",
			Latency: latency,
		}
	}
	
	return ConnectionStatus{
		Success: true,
		Message: "Connected successfully",
		Details: fmt.Sprintf("LM Studio server at %s:%s", host, port),
		Latency: latency,
	}
}

// testOllama tests connection to Ollama server
func testOllama(config ProviderConfig) ConnectionStatus {
	host := config.Host
	if host == "" {
		host = "localhost"
	}
	port := config.Port
	if port == "" {
		port = "11434"
	}
	
	url := fmt.Sprintf("http://%s:%s/api/tags", host, port)
	start := time.Now()
	
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Get(url)
	latency := time.Since(start)
	
	if err != nil {
		return ConnectionStatus{
			Success: false,
			Message: "Connection failed", 
			Details: err.Error(),
			Latency: latency,
		}
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != 200 {
		return ConnectionStatus{
			Success: false,
			Message: fmt.Sprintf("HTTP %d", resp.StatusCode),
			Details: "Ollama server returned error",
			Latency: latency,
		}
	}
	
	// Try to parse JSON response to verify it's a valid Ollama endpoint
	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return ConnectionStatus{
			Success: false,
			Message: "Invalid response",
			Details: "Server response is not valid JSON",
			Latency: latency,
		}
	}
	
	return ConnectionStatus{
		Success: true,
		Message: "Connected successfully",
		Details: fmt.Sprintf("Ollama server at %s:%s", host, port),
		Latency: latency,
	}
}

// testOpenAI tests connection to OpenAI API
func testOpenAI(config ProviderConfig) ConnectionStatus {
	if config.APIKey == "" {
		return ConnectionStatus{
			Success: false,
			Message: "API key required",
			Details: "OpenAI provider requires an API key",
		}
	}
	
	baseURL := config.BaseURL
	if baseURL == "" {
		baseURL = "https://api.openai.com"
	}
	
	url := baseURL + "/v1/models"
	start := time.Now()
	
	client := &http.Client{Timeout: 15 * time.Second}
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return ConnectionStatus{
			Success: false,
			Message: "Request creation failed",
			Details: err.Error(),
		}
	}
	
	req.Header.Set("Authorization", "Bearer "+config.APIKey)
	if config.OrgID != "" {
		req.Header.Set("OpenAI-Organization", config.OrgID)
	}
	
	resp, err := client.Do(req)
	latency := time.Since(start)
	
	if err != nil {
		return ConnectionStatus{
			Success: false,
			Message: "Connection failed",
			Details: err.Error(),
			Latency: latency,
		}
	}
	defer resp.Body.Close()
	
	if resp.StatusCode == 401 {
		return ConnectionStatus{
			Success: false,
			Message: "Authentication failed",
			Details: "Invalid API key or organization ID",
			Latency: latency,
		}
	}
	
	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return ConnectionStatus{
			Success: false,
			Message: fmt.Sprintf("HTTP %d", resp.StatusCode),
			Details: string(body),
			Latency: latency,
		}
	}
	
	// Try to parse JSON response
	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return ConnectionStatus{
			Success: false,
			Message: "Invalid response",
			Details: "API response is not valid JSON",
			Latency: latency,
		}
	}
	
	// Check if response has models field (expected OpenAI API structure)
	if _, hasModels := result["data"]; !hasModels {
		return ConnectionStatus{
			Success: false,
			Message: "Unexpected response",
			Details: "API response doesn't match OpenAI format",
			Latency: latency,
		}
	}
	
	endpoint := strings.TrimSuffix(baseURL, "/")
	return ConnectionStatus{
		Success: true,
		Message: "Connected successfully",
		Details: fmt.Sprintf("OpenAI API at %s", endpoint),
		Latency: latency,
	}
}