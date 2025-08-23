package providers

// Canonical provider names.
const (
    Local     = "local"
    LMStudio  = "lmstudio"
    Ollama    = "ollama"
    OpenAI    = "openai"
    ClaudeCLI = "claude-cli"
    OpenAICLI = "openai-cli"
)

// List returns the supported providers in display order.
func List() []string {
    return []string{Local, LMStudio, Ollama, OpenAI, ClaudeCLI, OpenAICLI}
}

