package providers

import (
    "encoding/json"
    "os/exec"
)

// ProviderInfo mirrors the CLI JSON for `chi-llm providers list --json`.
type ProviderInfo struct {
    Type        string `json:"type"`
    Implemented bool   `json:"implemented"`
}

// FetchTypes calls the chi-llm CLI to obtain supported provider types.
func FetchTypes() ([]string, error) {
    cmd := exec.Command("chi-llm", "providers", "list", "--json")
    out, err := cmd.Output()
    if err != nil {
        return nil, err
    }
    var items []ProviderInfo
    if err := json.Unmarshal(out, &items); err != nil {
        return nil, err
    }
    types := make([]string, 0, len(items))
    for _, it := range items {
        if it.Implemented && it.Type != "" {
            types = append(types, it.Type)
        }
    }
    return types, nil
}
