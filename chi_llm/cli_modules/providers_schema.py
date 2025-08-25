"""Provider field schemas for UI/automation (split out to keep file sizes small)."""

PROVIDER_SCHEMAS = {
    "local": {
        "fields": [
            {
                "name": "model",
                "type": "string",
                "required": False,
                "help": "Model ID (GGUF)",
            },
            {
                "name": "model_path",
                "type": "string",
                "required": False,
                "help": "Absolute path to GGUF model file",
            },
            {
                "name": "context_window",
                "type": "int",
                "required": False,
                "help": "Override context window (n_ctx)",
            },
            {
                "name": "n_gpu_layers",
                "type": "int",
                "required": False,
                "help": "Layers offloaded to GPU",
            },
            {
                "name": "output_tokens",
                "type": "int",
                "required": False,
                "help": "Default max output tokens",
            },
        ]
    },
    "local-zeroconfig": {
        "fields": [
            {
                "name": "model",
                "type": "string",
                "required": False,
                "help": "Recommended model ID from curated list",
            }
        ]
    },
    "local-custom": {
        "fields": [
            {
                "name": "model_path",
                "type": "string",
                "required": False,
                "help": "Absolute path to GGUF model file",
            },
            {
                "name": "model",
                "type": "string",
                "required": False,
                "help": "Model ID (optional; overrides default)",
            },
            {
                "name": "context_window",
                "type": "int",
                "required": False,
                "help": "Override context window (n_ctx)",
            },
            {
                "name": "n_gpu_layers",
                "type": "int",
                "required": False,
                "help": "Layers offloaded to GPU",
            },
            {
                "name": "output_tokens",
                "type": "int",
                "required": False,
                "help": "Default max output tokens",
            },
        ]
    },
    "lmstudio": {
        "fields": [
            {
                "name": "host",
                "type": "string",
                "required": False,
                "default": "localhost",
                "help": "Server host",
            },
            {
                "name": "port",
                "type": "int",
                "required": False,
                "default": 1234,
                "help": "Server port",
            },
            {
                "name": "model",
                "type": "string",
                "required": False,
                "help": "Default model ID",
            },
        ]
    },
    "ollama": {
        "fields": [
            {
                "name": "host",
                "type": "string",
                "required": False,
                "default": "localhost",
                "help": "Server host",
            },
            {
                "name": "port",
                "type": "int",
                "required": False,
                "default": 11434,
                "help": "Server port",
            },
            {
                "name": "model",
                "type": "string",
                "required": False,
                "help": "Default model ID",
            },
        ]
    },
    "openai": {
        "fields": [
            {
                "name": "api_key",
                "type": "secret",
                "required": True,
                "help": "OpenAI API key",
            },
            {
                "name": "base_url",
                "type": "string",
                "required": False,
                "help": "API base URL",
            },
            {
                "name": "org_id",
                "type": "string",
                "required": False,
                "help": "Organization ID",
            },
            {
                "name": "model",
                "type": "string",
                "required": False,
                "help": "Default model ID",
            },
        ]
    },
    "anthropic": {
        "fields": [
            {
                "name": "api_key",
                "type": "secret",
                "required": True,
                "help": "Anthropic API key",
            },
            {
                "name": "model",
                "type": "string",
                "required": True,
                "help": "Default model ID (e.g., claude-3-haiku-20240307)",
            },
        ]
    },
    "claude-cli": {
        "fields": [
            {
                "name": "model",
                "type": "string",
                "required": False,
                "help": "Default model ID (if applicable)",
            },
        ]
    },
    "openai-cli": {
        "fields": [
            {
                "name": "model",
                "type": "string",
                "required": False,
                "help": "Default model ID (if applicable)",
            },
        ]
    },
}
