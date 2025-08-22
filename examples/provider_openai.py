"""
Example: Using OpenAI as an external provider.

Requires the OpenAI Python SDK:
    pip install openai

Set environment variables, then run:
    export CHI_LLM_PROVIDER_TYPE=openai
    export CHI_LLM_PROVIDER_API_KEY=sk-...
    export CHI_LLM_PROVIDER_MODEL=gpt-4o-mini
    python examples/provider_openai.py
"""

import os
from chi_llm import MicroLLM


def main():
    # Ensure env is set (or configure via `chi-llm providers set`)
    if not os.environ.get("CHI_LLM_PROVIDER_TYPE"):
        os.environ["CHI_LLM_PROVIDER_TYPE"] = "openai"
    if not os.environ.get("CHI_LLM_PROVIDER_MODEL"):
        os.environ["CHI_LLM_PROVIDER_MODEL"] = "gpt-4o-mini"

    llm = MicroLLM()
    print(llm.generate("Say hello from OpenAI in one sentence."))


if __name__ == "__main__":
    main()
