"""
Example: Using LM Studio as an external provider.

Requires LM Studio local server running (OpenAI-compatible API).

Start LM Studio server, then run:
    python examples/provider_lmstudio.py
"""

import os
from chi_llm import MicroLLM, list_provider_models


def main():
    # Configure provider via environment (respected by chi_llm.utils.load_config)
    os.environ["CHI_LLM_PROVIDER_TYPE"] = "lmstudio"
    os.environ["CHI_LLM_PROVIDER_HOST"] = "127.0.0.1"
    os.environ["CHI_LLM_PROVIDER_PORT"] = "1234"  # default LM Studio port
    # Optional: set explicit model exposed by LM Studio
    # os.environ["CHI_LLM_PROVIDER_MODEL"] = "qwen2.5-coder-1.5b"

    # Inspect models exposed by LM Studio (best-effort)
    models = list_provider_models()
    print("LM Studio models:", models[:3], "..." if len(models) > 3 else "")

    llm = MicroLLM()
    print(llm.generate("Say hello from LM Studio in one sentence."))


if __name__ == "__main__":
    main()
