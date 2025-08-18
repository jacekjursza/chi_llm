"""
chi_llm - AI-powered code analysis using Gemma 3 270M model.

A lightweight, privacy-focused code analyzer that runs completely offline
using Google's Gemma 3 270M model.

Basic usage:
    >>> from chi_llm import CodeAnalyzer
    >>> analyzer = CodeAnalyzer()
    >>> result = analyzer.analyze("def hello(): return 'world'")
    >>> print(result)

Advanced usage:
    >>> # Analyze with custom question
    >>> analyzer = CodeAnalyzer()
    >>> code = "def factorial(n): return 1 if n == 0 else n * factorial(n-1)"
    >>> result = analyzer.analyze(code, question="Is this implementation efficient?")
    
    >>> # Analyze file directly
    >>> result = analyzer.analyze_file("script.py", question="Find potential bugs")
"""

from .analyzer import (
    CodeAnalyzer,
    load_model,
    analyze_code,
    DEFAULT_QUESTION,
    MODEL_REPO,
    MODEL_FILE,
    MODEL_DIR
)

__version__ = "1.0.0"
__author__ = "AI Assistant"
__all__ = [
    "CodeAnalyzer",
    "load_model",
    "analyze_code",
    "DEFAULT_QUESTION",
    "MODEL_REPO",
    "MODEL_FILE",
    "MODEL_DIR"
]