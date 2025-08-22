"""Textual-based TUI for chi_llm configuration.

This package intentionally avoids importing Textual at module import time to
keep dependencies optional. The `launch_tui` function in `app.py` will import
Textual only when invoked by the CLI.
"""

from .store import TUIStore  # re-export for convenience

__all__ = ["TUIStore"]
