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
	if types, err := FetchTypes(); err == nil && len(types) > 0 {
		return types
	}
	// If CLI is unavailable or returned nothing, return empty to let caller handle.
	return []string{}
}
