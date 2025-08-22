"""
Example: Using Ollama as an external provider.

Requires Ollama running locally.

Start Ollama, then run:
    python examples/provider_ollama.py
"""

import os
from chi_llm import MicroLLM, list_provider_models


def main():
    # Configure provider via environment
    os.environ["CHI_LLM_PROVIDER_TYPE"] = "ollama"
    os.environ["CHI_LLM_PROVIDER_HOST"] = "127.0.0.1"
    os.environ["CHI_LLM_PROVIDER_PORT"] = "11434"  # default Ollama port
    # Optional: set explicit model installed in Ollama
    # os.environ["CHI_LLM_PROVIDER_MODEL"] = "llama3.2:latest"

    # Inspect installed models in Ollama (best-effort)
    models = list_provider_models()
    print("Ollama models:", models[:3], "..." if len(models) > 3 else "")

    llm = MicroLLM()
    print(llm.generate("Say hello from Ollama in one sentence."))


if __name__ == "__main__":
    main()
