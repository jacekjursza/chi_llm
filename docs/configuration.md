# Configuration Guide

chi_llm supports flexible configuration management with a clear hierarchy that allows both zero-configuration usage and fine-grained control per project.

## Configuration Hierarchy

Configuration sources are checked in this order (highest priority first):

### 1. Environment Variables (Highest Priority)
Override any setting via environment:

```bash
# Set model for current session
export CHI_LLM_MODEL=phi3-mini

# Point to custom config file
export CHI_LLM_CONFIG=/path/to/custom/config.json

# Adjust context window
export CHI_LLM_CONTEXT=16384

# Set max response tokens
export CHI_LLM_MAX_TOKENS=2048
```

Perfect for:
- CI/CD pipelines
- Docker containers
- Temporary overrides
- Testing different models

### 2. Local Project Config
`.chi_llm.json` in current working directory:

```json
{
  "default_model": "qwen3-1.7b",
  "preferred_context": 32768,
  "preferred_max_tokens": 4096,
  "downloaded_models": ["qwen3-1.7b", "phi3-mini"]
}
```

Use cases:
- Project-specific model requirements
- Team-shared settings (commit to repo)
- Override global preferences per project

### 3. Parent Project Config
Searches up the directory tree for `.chi_llm.json`:

```
/monorepo
  /.chi_llm.json          <- Found and used
  /services
    /api
      /src                 <- Working here
        main.py
```

Benefits:
- Monorepo configurations
- Workspace-wide settings
- Nested project inheritance

### 4. Global User Config
`~/.cache/chi_llm/model_config.json`:

```json
{
  "default_model": "gemma-270m",
  "downloaded_models": ["gemma-270m", "phi3-mini", "qwen3-1.7b"],
  "preferred_context": 32768,
  "preferred_max_tokens": 4096
}
```

Set via:
- `chi-llm setup` - Interactive wizard
- `chi-llm models set <model>` - Set default model
- Direct editing (JSON file)

### 5. Built-in Defaults (Lowest Priority)
Zero-configuration defaults:
- Model: `gemma-270m` (ultra-lightweight, 200MB)
- Context: 32,768 tokens (full model capacity)
- Max tokens: 4,096 (default response length)
- Temperature: 0.7

## CLI Configuration Management

### View Current Configuration

```bash
# Show current model and config source
chi-llm models current

# Output:
# Phi-3 Mini (3.8B) [CURRENT]
#   ID: phi3-mini
#   ...
# 
# 📁 Config source: local
#    Path: /project/.chi_llm.json
```

### Set Default Model

```bash
# Set globally (all projects)
chi-llm models set phi3-mini

# Set locally (current project only)
chi-llm models set phi3-mini --local

# Creates/updates .chi_llm.json in current directory
```

### Interactive Setup

```bash
# Run setup wizard
chi-llm setup

# Features:
# - System RAM detection
# - Model recommendations
# - Download management
# - Configuration saving
```

## Python API Configuration

### Basic Usage (Zero Config)

```python
from chi_llm import MicroLLM

# Uses configuration hierarchy automatically:
# - Honors per-project default_model from .chi_llm.json/.yaml
# - Honors CHI_LLM_MODEL env var
# - Falls back to built-in defaults when no config
llm = MicroLLM()
```

### Explicit Model Selection

```python
# Override with specific model
llm = MicroLLM(model_id="phi3-mini")

# Custom parameters
llm = MicroLLM(
    model_id="qwen3-1.7b",
    temperature=0.3,
    max_tokens=2048
)
```

### Custom Model Path

```python
# Use your own GGUF model
llm = MicroLLM(model_path="/path/to/model.gguf")
```

## Configuration Examples

### Example 1: Development vs Production

Development (`.chi_llm.json`):
```json
{
  "default_model": "gemma-270m",
  "preferred_max_tokens": 1024
}
```

Production (via environment):
```bash
export CHI_LLM_MODEL=phi3-mini
export CHI_LLM_MAX_TOKENS=4096
```

### Example 2: Team Collaboration

Shared team config (`.chi_llm.json` in repo):
```json
{
  "default_model": "qwen3-1.7b",
  "preferred_context": 32768,
  "preferred_max_tokens": 4096
}
```

Personal override (environment):
```bash
# Use better model locally if you have more RAM
export CHI_LLM_MODEL=phi3-mini
```

### Example 3: CI/CD Pipeline

```yaml
# .github/workflows/test.yml
env:
  CHI_LLM_MODEL: gemma-270m  # Fast model for CI
  CHI_LLM_MAX_TOKENS: 512    # Faster tests

steps:
  - run: pytest tests/
```

### Example 4: Docker Deployment

```dockerfile
FROM python:3.9

# Install chi_llm
RUN pip install chi-llm

# Set production model
ENV CHI_LLM_MODEL=phi3-mini
ENV CHI_LLM_CONTEXT=4096

# Your app
COPY . /app
CMD ["python", "/app/main.py"]
```

## Best Practices

1. **Don't commit global config** - Keep `~/.cache/chi_llm/` in `.gitignore`

2. **Use local config for projects** - Create `.chi_llm.json` for project-specific needs

3. **Environment for overrides** - Use env vars for temporary changes or CI/CD

4. **Document model requirements** - Note in README which models your project needs

5. **Test with minimal model** - Use `gemma-270m` for unit tests (fast, small)

## Troubleshooting

## Provider Configuration (Draft)

chi_llm supports multiple backends via a minimal provider abstraction. The default is local llama.cpp with GGUF models. You can declare a provider in config or via environment variables.

### Config File

YAML:
```yaml
provider:
  type: local            # one of: local, lmstudio, ollama, openai, anthropic, groq, gemini
  model: qwen3-1.7b      # backend-specific id (for local, matches MODELS registry)
  host: localhost        # when relevant (e.g., LM Studio / Ollama / custom server)
  port: 11434            # optional
  api_key: ${API_KEY}    # for external providers (if needed)
```

JSON:
```json
{
  "provider": {
    "type": "local",
    "model": "qwen3-1.7b",
    "host": "localhost",
    "port": 11434,
    "api_key": "your-key-here"
  }
}
```

Notes:
- If `type` is `local` and `model` is provided, `MicroLLM` uses it when `model_id` isn’t passed explicitly.
- Non-local providers are added incrementally; using an unimplemented provider type will raise a clear runtime error once integrated.

### Environment Variables

```bash
export CHI_LLM_PROVIDER_TYPE=local
export CHI_LLM_PROVIDER_MODEL=qwen3-1.7b
export CHI_LLM_PROVIDER_HOST=localhost
export CHI_LLM_PROVIDER_PORT=11434
export CHI_LLM_PROVIDER_API_KEY=sk-...
```

Environment variables override file configuration and are safe to use for CI/CD or local overrides.

### LM Studio

LM Studio exposes an OpenAI-compatible local server (default `127.0.0.1:1234`).
Enable it in LM Studio (Settings → Server), then set chi_llm to use it:

YAML:
```yaml
provider:
  type: lmstudio
  host: 127.0.0.1
  port: 1234
  model: my-local-model  # name as shown in LM Studio
```

Environment:
```bash
export CHI_LLM_PROVIDER_TYPE=lmstudio
export CHI_LLM_PROVIDER_HOST=127.0.0.1
export CHI_LLM_PROVIDER_PORT=1234
export CHI_LLM_PROVIDER_MODEL=my-local-model
```

Usage stays the same in code; MicroLLM automatically routes calls:
```python
from chi_llm import MicroLLM

llm = MicroLLM()
print(llm.generate("Hello from LM Studio"))
```

If LM Studio isn’t reachable, errors include the base URL and guidance to start the server.

### Ollama

Ollama runs a local server by default on `127.0.0.1:11434`.
Set chi_llm to use it:

YAML:
```yaml
provider:
  type: ollama
  host: 127.0.0.1
  port: 11434
  model: llama3.2:latest  # or any pulled model name
```

Environment:
```bash
export CHI_LLM_PROVIDER_TYPE=ollama
export CHI_LLM_PROVIDER_HOST=127.0.0.1
export CHI_LLM_PROVIDER_PORT=11434
export CHI_LLM_PROVIDER_MODEL=llama3.2:latest
```

The API stays the same:
```python
from chi_llm import MicroLLM

llm = MicroLLM()
print(llm.chat("Hello, Ollama!"))
```

If Ollama is not reachable, errors include the base URL and a hint to run `ollama serve`.

### Check Config Source

```bash
# See where config is coming from
chi-llm models current
```

### Reset to Defaults

```bash
# Remove local config
rm .chi_llm.json

# Remove global config
rm ~/.cache/chi_llm/model_config.json
```

### Force Specific Config

```bash
# Use specific config file
export CHI_LLM_CONFIG=/path/to/config.json
python your_script.py
```

## Configuration Schema

Complete configuration file schema:

```json
{
  "default_model": "string (model ID, default: gemma-270m)",
  "downloaded_models": ["array", "of", "model", "ids"],
  "preferred_context": "number (tokens, default: 32768)",
  "preferred_max_tokens": "number (tokens, default: 4096)",
  "temperature": "number (0.0-1.0, optional, default: 0.7)",
  "top_p": "number (0.0-1.0, optional)",
  "top_k": "number (optional)",
  "provider": {
    "type": "string (local|lmstudio|ollama|openai|anthropic|groq|gemini)",
    "model": "string (backend-specific id)",
    "host": "string (optional)",
    "port": "number|string (optional)",
    "api_key": "string (optional)"
  }
}
```

Note: Not all fields are required. Missing fields use defaults from lower priority sources.
