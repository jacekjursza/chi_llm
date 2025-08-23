package tui

import (
    "encoding/json"
    "os"
    "os/exec"
    "path/filepath"
    "strings"
    "time"
)

// Diagnostics holds a minimal snapshot of configuration and environment hints.
type Diagnostics struct {
    Timestamp    string            `json:"timestamp"`
    CWD          string            `json:"cwd"`
    ConfigPath   string            `json:"config_path"`
    ProviderType string            `json:"provider_type"`
    ProviderModel string           `json:"provider_model,omitempty"`
    Env          map[string]string `json:"env"`
    Hints        []string          `json:"hints"`
}

// CollectDiagnostics reads a local project config (if present) and inspects
// basic environment to generate user-facing hints without any network calls.
func CollectDiagnostics() Diagnostics {
    wd, _ := os.Getwd()
    cfgPath := filepath.Join(wd, ".chi_llm.json")
    var provType, provModel string
    if b, err := os.ReadFile(cfgPath); err == nil && len(b) > 0 {
        // reuse the local struct shape from config.go
        var pc projectConfig
        if json.Unmarshal(b, &pc) == nil {
            if t, _ := pc.Provider["type"].(string); t != "" {
                provType = t
            }
            if m, _ := pc.Provider["model"].(string); m != "" {
                provModel = m
            }
        }
    } else {
        cfgPath = ""
    }

    env := map[string]string{}
    hints := []string{}

    switch provType {
    case "openai":
        if v := strings.TrimSpace(os.Getenv("OPENAI_API_KEY")); v != "" {
            env["OPENAI_API_KEY"] = "set"
        } else {
            env["OPENAI_API_KEY"] = "missing"
            hints = append(hints, "Set OPENAI_API_KEY for OpenAI provider")
        }
    case "ollama":
        if _, err := exec.LookPath("ollama"); err == nil {
            env["ollama"] = "found"
        } else {
            env["ollama"] = "not-found"
            hints = append(hints, "Install Ollama and ensure it is on PATH")
        }
        if v := strings.TrimSpace(os.Getenv("OLLAMA_HOST")); v != "" {
            env["OLLAMA_HOST"] = v
        }
    case "lmstudio":
        if v := strings.TrimSpace(os.Getenv("LMSTUDIO_BASE_URL")); v != "" {
            env["LMSTUDIO_BASE_URL"] = v
        } else {
            hints = append(hints, "Optionally set LMSTUDIO_BASE_URL (default http://localhost:1234)")
        }
    case "", "local", "llamacpp":
        hints = append(hints, "Local provider requires no API keys")
    }

    return Diagnostics{
        Timestamp:     time.Now().Format(time.RFC3339),
        CWD:           wd,
        ConfigPath:    cfgPath,
        ProviderType:  provType,
        ProviderModel: provModel,
        Env:           env,
        Hints:         hints,
    }
}

// ExportDiagnostics writes diagnostics to the given path (or default filename)
// and returns the absolute path.
func ExportDiagnostics(filename string, d Diagnostics) (string, error) {
    if strings.TrimSpace(filename) == "" {
        filename = "chi_llm_diagnostics.json"
    }
    b, err := json.MarshalIndent(d, "", "  ")
    if err != nil {
        return "", err
    }
    if err := os.WriteFile(filename, b, 0o644); err != nil {
        return "", err
    }
    abs, _ := filepath.Abs(filename)
    return abs, nil
}

