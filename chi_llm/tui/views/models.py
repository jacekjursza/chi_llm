"""Models view for the Textual TUI.

MVP: render a simple list of models with basic keybindings.
"""

from typing import List


def _format_model_row(m: dict) -> str:
    mark = "✅" if m.get("downloaded") else "  "
    parts = [
        f"{mark} {m.get('id')}",
        f"{m.get('size','')}",
        f"ctx={m.get('context_window','?')}",
        f"RAM≈{m.get('recommended_ram_gb','?')}GB",
    ]
    return "  ".join(parts)


def build_models_text(store) -> List[str]:
    """Return formatted lines for models list (no Textual dependency for tests)."""
    items = store.list_models(show_all=True)
    rows = [_format_model_row(m) for m in items]
    return rows


# The actual Textual view is imported lazily in the app to keep tests light.
