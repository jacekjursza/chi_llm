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
from .core import MicroLLM, quick_llm, MODEL_REPO, MODEL_FILE, MODEL_DIR

# Prompt templates
from .prompts import PromptTemplates, code_prompt, data_prompt

# Utilities
from .utils import (
    truncate_text,
    format_chat_history,
    clean_response,
    get_model_info,
)
from .config import (
    load_config as load_config,  # stable SDK import path
    resolve_model,
    get_provider_settings,
)
from .providers.discovery import list_provider_models  # type: ignore

# Model registry helpers (programmatic access)
from .models import ModelManager, MODELS, ModelInfo  # type: ignore

# Backward compatibility imports kept near top to satisfy linters
from .analyzer import (
    CodeAnalyzer,
    load_model,
    analyze_code,
    DEFAULT_QUESTION,
)


def list_available_models(show_all: bool = True):
    """Return a list of available models with minimal metadata.

    Each item: {id, name, size, context_window, downloaded: bool}
    """
    mgr = ModelManager()
    items = mgr.list_models(show_all=show_all)
    out = []
    for m in items:
        try:
            downloaded = mgr.is_downloaded(m.id)
        except Exception:
            downloaded = False
        out.append(
            {
                "id": m.id,
                "name": m.name,
                "size": m.size,
                "context_window": m.context_window,
                "downloaded": downloaded,
            }
        )
    return out


def get_current_model_status():
    """Return current model id and status.

    Returns: {id, name, downloaded: bool, path: str | ''}
    """
    mgr = ModelManager()
    cur = mgr.get_current_model()
    downloaded = mgr.is_downloaded(cur.id)
    path = mgr.get_model_path(cur.id)
    return {
        "id": cur.id,
        "name": cur.name,
        "downloaded": downloaded,
        "path": str(path or ""),
    }


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
    # Config provider API
    "resolve_model",
    "get_provider_settings",
    # Registry helpers
    "ModelManager",
    "ModelInfo",
    "MODELS",
    "list_available_models",
    "get_current_model_status",
    "list_provider_models",
    # Backward compatibility
    "CodeAnalyzer",
    "load_model",
    "analyze_code",
    # Constants
    "MODEL_REPO",
    "MODEL_FILE",
    "MODEL_DIR",
    "DEFAULT_QUESTION",
]
