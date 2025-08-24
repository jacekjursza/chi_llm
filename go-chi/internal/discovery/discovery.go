package discovery

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os/exec"
	"strings"
	"time"
)

// ModelInfo represents a provider model entry.
type ModelInfo struct {
	ID    string
	SizeB int64 // 0 when unknown
}

func (m ModelInfo) SizeMB() int64 {
	if m.SizeB <= 0 {
		return 0
	}
	return m.SizeB / (1024 * 1024)
}

// LocalModelDetail reflects chi-llm models list --json payload fields
// used by the Go TUI for the local provider.
type LocalModelDetail struct {
	ID               string   `json:"id"`
	Name             string   `json:"name"`
	Size             string   `json:"size"`
	FileSizeMB       int      `json:"file_size_mb"`
	ContextWindow    int      `json:"context_window"`
	RecommendedRAMGB float64  `json:"recommended_ram_gb"`
	Tags             []string `json:"tags"`
	Downloaded       bool     `json:"downloaded"`
	Current          bool     `json:"current"`
}

// GetAvailableRAMGB reads available RAM from chi-llm CLI stats
// via `chi-llm models current --explain --json`.
func GetAvailableRAMGB() (float64, error) {
	cmd := exec.Command("chi-llm", "models", "current", "--explain", "--json")
	out, err := cmd.Output()
	if err != nil {
		return 0, err
	}
	var payload map[string]any
	if err := json.Unmarshal(out, &payload); err != nil {
		return 0, err
	}
	if v, ok := payload["available_ram_gb"]; ok {
		switch t := v.(type) {
		case float64:
			return t, nil
		case int:
			return float64(t), nil
		}
	}
	return 0, nil
}

// LMStudioModels lists models via OpenAI-compatible /v1/models.
// base should be a host:port or full base URL; http:// is added if missing.
func LMStudioModels(base string) ([]ModelInfo, error) {
	baseURL := ensureBase(base)
	url := strings.TrimRight(baseURL, "/") + "/v1/models"
	client := http.Client{Timeout: 3 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode/100 != 2 {
		return nil, fmt.Errorf("lmstudio: http %d", resp.StatusCode)
	}
	var payload struct {
		Data []struct {
			ID string `json:"id"`
		} `json:"data"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return nil, err
	}
	out := make([]ModelInfo, 0, len(payload.Data))
	for _, d := range payload.Data {
		if d.ID == "" {
			continue
		}
		out = append(out, ModelInfo{ID: d.ID})
	}
	return out, nil
}

// OllamaModels lists models via /api/tags.
func OllamaModels(base string) ([]ModelInfo, error) {
	baseURL := ensureBase(base)
	url := strings.TrimRight(baseURL, "/") + "/api/tags"
	client := http.Client{Timeout: 3 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode/100 != 2 {
		return nil, fmt.Errorf("ollama: http %d", resp.StatusCode)
	}
	var payload struct {
		Models []struct {
			Name string `json:"name"`
			Size int64  `json:"size"`
		} `json:"models"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return nil, err
	}
	out := make([]ModelInfo, 0, len(payload.Models))
	for _, m := range payload.Models {
		if m.Name == "" {
			continue
		}
		out = append(out, ModelInfo{ID: m.Name, SizeB: m.Size})
	}
	return out, nil
}

func ensureBase(b string) string {
	if b == "" {
		return "http://127.0.0.1:1234"
	}
	if strings.HasPrefix(b, "http://") || strings.HasPrefix(b, "https://") {
		return b
	}
	return "http://" + b
}

// LocalModels returns a list of commonly available local GGUF models.
// In a real implementation, this would scan the model directory.
func LocalModels() ([]ModelInfo, error) {
	// Return some common local models as placeholders
	return []ModelInfo{
		{ID: "gemma-270m", SizeB: 200 * 1024 * 1024},  // 200MB
		{ID: "qwen3-1.7b", SizeB: 1700 * 1024 * 1024}, // 1.7GB
		{ID: "phi3-mini", SizeB: 3800 * 1024 * 1024},  // 3.8GB
		{ID: "llama3-8b", SizeB: 8000 * 1024 * 1024},  // 8GB
	}, nil
}

// CliLocalModels shells out to `chi-llm models list --json` to obtain
// the curated local models catalog from the Python CLI.
// Falls back to LocalModels when the CLI is not available.
func CliLocalModels() ([]ModelInfo, error) {
	cmd := exec.Command("chi-llm", "models", "list", "--json")
	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("chi-llm not available: %w", err)
	}
	var models []struct {
		ID         string `json:"id"`
		FileSizeMB int64  `json:"file_size_mb"`
	}
	if err := json.Unmarshal(out, &models); err != nil {
		return nil, fmt.Errorf("parse models json: %w", err)
	}
	res := make([]ModelInfo, 0, len(models))
	for _, m := range models {
		sizeB := m.FileSizeMB * 1024 * 1024
		res = append(res, ModelInfo{ID: m.ID, SizeB: sizeB})
	}
	return res, nil
}

// CliLocalModelDetails shells out to `chi-llm models list --json` and parses
// the full local models payload with metadata and flags.
func CliLocalModelDetails() ([]LocalModelDetail, error) {
	cmd := exec.Command("chi-llm", "models", "list", "--json")
	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("chi-llm not available: %w", err)
	}
	var models []LocalModelDetail
	if err := json.Unmarshal(out, &models); err != nil {
		return nil, fmt.Errorf("parse models json: %w", err)
	}
	return models, nil
}

// Discover lists models for provider type (local|lmstudio|ollama) using default ports when host blank.
func Discover(provider, host string, port int) ([]ModelInfo, error) {
	switch provider {
	case "local":
		if got, err := CliLocalModels(); err == nil {
			return got, nil
		}
		return LocalModels()
	case "lmstudio":
		if port == 0 {
			port = 1234
		}
		return LMStudioModels(fmt.Sprintf("%s:%d", hostOrLocal(host), port))
	case "ollama":
		if port == 0 {
			port = 11434
		}
		return OllamaModels(fmt.Sprintf("%s:%d", hostOrLocal(host), port))
	default:
		return nil, errors.New("unsupported provider for discovery")
	}
}

func hostOrLocal(h string) string {
	if strings.TrimSpace(h) == "" {
		return "127.0.0.1"
	}
	return h
}
