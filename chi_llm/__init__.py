"""
chi_llm - Zero Configuration Micro-LLM Library for Python

The simplest way to add AI to your Python project. No API keys, no cloud dependencies,
no complex setup. Just import and use.

Quick start:
    >>> from chi_llm import MicroLLM
    >>> llm = MicroLLM()
    >>> response = llm.generate("Hello, how are you?")
    >>> print(response)

Even quicker:
    >>> from chi_llm import quick_llm
    >>> print(quick_llm("Write a haiku about Python"))

Common use cases:
    >>> # Chat conversation
    >>> llm.chat("What's the weather like?")
    
    >>> # Text completion
    >>> llm.complete("The quick brown fox")
    
    >>> # Question answering
    >>> llm.ask("What is Python?")
    
    >>> # Code analysis (backward compatible)
    >>> llm.analyze("def hello(): return 'world'")
    
    >>> # Data extraction
    >>> llm.extract("John is 30 years old", format="json")
    
    >>> # Summarization
    >>> llm.summarize(long_text, max_sentences=3)
"""

# New primary API
from .core import (
    MicroLLM,
    quick_llm,
    MODEL_REPO,
    MODEL_FILE,
    MODEL_DIR
)

# Prompt templates
from .prompts import (
    PromptTemplates,
    code_prompt,
    data_prompt
)

# Utilities
from .utils import (
    load_config,
    truncate_text,
    format_chat_history,
    clean_response,
    get_model_info
)

# Backward compatibility
from .analyzer import (
    CodeAnalyzer,
    load_model,
    analyze_code,
    DEFAULT_QUESTION
)

__version__ = "2.1.0"
__author__ = "Jacek Jursza"
__all__ = [
    # Primary API
    "MicroLLM",
    "quick_llm",
    
    # Prompts
    "PromptTemplates",
    "code_prompt",
    "data_prompt",
    
    # Utils
    "load_config",
    "truncate_text",
    "format_chat_history",
    "clean_response",
    "get_model_info",
    
    # Backward compatibility
    "CodeAnalyzer",
    "load_model",
    "analyze_code",
    
    # Constants
    "MODEL_REPO",
    "MODEL_FILE",
    "MODEL_DIR",
    "DEFAULT_QUESTION"
]