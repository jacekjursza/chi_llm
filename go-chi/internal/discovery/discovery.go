package discovery

import (
    "encoding/json"
    "errors"
    "fmt"
    "net/http"
    "strings"
    "time"
)

// ModelInfo represents a provider model entry.
type ModelInfo struct {
    ID     string
    SizeB  int64 // 0 when unknown
}

func (m ModelInfo) SizeMB() int64 {
    if m.SizeB <= 0 { return 0 }
    return m.SizeB / (1024 * 1024)
}

// LMStudioModels lists models via OpenAI-compatible /v1/models.
// base should be a host:port or full base URL; http:// is added if missing.
func LMStudioModels(base string) ([]ModelInfo, error) {
    baseURL := ensureBase(base)
    url := strings.TrimRight(baseURL, "/") + "/v1/models"
    client := http.Client{ Timeout: 3 * time.Second }
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
        if d.ID == "" { continue }
        out = append(out, ModelInfo{ID: d.ID})
    }
    return out, nil
}

// OllamaModels lists models via /api/tags.
func OllamaModels(base string) ([]ModelInfo, error) {
    baseURL := ensureBase(base)
    url := strings.TrimRight(baseURL, "/") + "/api/tags"
    client := http.Client{ Timeout: 3 * time.Second }
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
        if m.Name == "" { continue }
        out = append(out, ModelInfo{ID: m.Name, SizeB: m.Size})
    }
    return out, nil
}

func ensureBase(b string) string {
    if b == "" { return "http://127.0.0.1:1234" }
    if strings.HasPrefix(b, "http://") || strings.HasPrefix(b, "https://") { return b }
    return "http://" + b
}

// Discover lists models for provider type (lmstudio|ollama) using default ports when host blank.
func Discover(provider, host string, port int) ([]ModelInfo, error) {
    switch provider {
    case "lmstudio":
        if port == 0 { port = 1234 }
        return LMStudioModels(fmt.Sprintf("%s:%d", hostOrLocal(host), port))
    case "ollama":
        if port == 0 { port = 11434 }
        return OllamaModels(fmt.Sprintf("%s:%d", hostOrLocal(host), port))
    default:
        return nil, errors.New("unsupported provider for discovery")
    }
}

func hostOrLocal(h string) string {
    if strings.TrimSpace(h) == "" { return "127.0.0.1" }
    return h
}

