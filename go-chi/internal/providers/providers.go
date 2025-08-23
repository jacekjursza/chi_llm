package providers

// Canonical provider names.
const (
    LlamaCPP = "llamacpp"
    LMStudio = "lmstudio"
    Ollama   = "ollama"
)

// List returns the supported providers in display order.
func List() []string {
    return []string{LlamaCPP, LMStudio, Ollama}
}

