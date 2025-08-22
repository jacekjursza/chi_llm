"""
Example: Routing between multiple providers using profiles and tags.

This example defines provider profiles inline via CHI_LLM_CONFIG (JSON),
then uses tags on MicroLLM to select the appropriate provider.

Run with optionally running LM Studio/Ollama; the router will fall back
when a provider is unavailable.
"""

import json
import os
from chi_llm import MicroLLM


def main():
    profiles = [
        {
            "name": "fast-local-ollama",
            "type": "ollama",
            "host": "127.0.0.1",
            "port": 11434,
            "model": "llama3.2:latest",
            "tags": ["fast", "cpu"],
            "priority": 50,
        },
        {
            "name": "quality-lmstudio",
            "type": "lmstudio",
            "host": "127.0.0.1",
            "port": 1234,
            "model": "qwen2.5-coder-1.5b",
            "tags": ["quality"],
            "priority": 40,
        },
        # Add more providers here if desired
    ]

    # Inject profiles via env without writing files
    os.environ["CHI_LLM_CONFIG"] = json.dumps({"provider_profiles": profiles})

    # Choose by tags (router selects first matching by priority)
    llm = MicroLLM()
    llm.tags = ["quality"]
    print("[quality]", llm.generate("One sentence self-introduction."))

    llm.tags = ["fast"]
    print("[fast]", llm.generate("One sentence about routing."))


if __name__ == "__main__":
    main()
