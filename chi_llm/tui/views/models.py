"""Models view helpers and controller for the Textual TUI.

This module is intentionally UI-framework agnostic to keep tests simple.
It exposes small utilities for formatting and a controller that bridges
user intents to the store layer (set default model, download model, etc.).
"""

from typing import List, Dict, Any, Optional


def _format_model_row(m: Dict[str, Any]) -> str:
    mark = "✅" if m.get("downloaded") else "  "
    parts = [
        f"{mark} {m.get('id')}",
        f"{m.get('size', '')}",
        f"ctx={m.get('context_window', '?')}",
        f"RAM≈{m.get('recommended_ram_gb', '?')}GB",
    ]
    return "  ".join(parts)


def build_models_text(store) -> List[str]:
    """Return formatted lines for models list.

    No Textual dependency here; purely string formatting so we can unit test
    without a terminal.
    """
    items = store.list_models(show_all=True)
    rows = [_format_model_row(m) for m in items]
    return rows


def format_model_details(m: Dict[str, Any]) -> List[str]:
    """Return a detailed multi-line description of a model for display."""
    tags = ", ".join(m.get("tags") or [])
    return [
        f"ID: {m.get('id')}",
        f"Name: {m.get('name', '')}",
        f"Size: {m.get('size', '')} ({m.get('file_size_mb', '?')} MB)",
        f"Context: {m.get('context_window', '?')}",
        f"RAM (rec.): {m.get('recommended_ram_gb', '?')} GB",
        f"Tags: {tags}",
        f"Downloaded: {'yes' if m.get('downloaded') else 'no'}",
    ]


class ModelsController:
    """Bridge user intents to the store for models operations.

    This abstraction allows unit tests to verify that the correct store
    methods are invoked without needing to run a Textual application.
    """

    def __init__(self, store) -> None:
        self.store = store

    def list(self) -> List[Dict[str, Any]]:
        return self.store.list_models(show_all=True)

    def set_default(self, model_id: str, scope: str = "local") -> Dict[str, Any]:
        """Set default model via store and return the new current model."""
        # scope: "local" writes to project .chi_llm.json, "global" to user config
        return self.store.set_default_model(model_id, scope=scope)

    def download(self, model_id: str) -> str:
        """Download a model via store; return the local file path."""
        return self.store.download_model(model_id)


# The actual Textual view (widgets, keybindings) is created in app.py and may
# use these helpers for rendering and actions.


def create_models_view(store) -> "object":  # return a Textual Widget instance
    """Create an interactive Models view (List + Details) bound to store.

    Imported lazily by the TUI app so tests don't require Textual.
    """
    from textual.app import ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import ListView, ListItem, Label, Static
    from textual.reactive import reactive

    ctrl = ModelsController(store)
    models_cache: List[Dict[str, Any]] = ctrl.list()

    class ModelsView(Horizontal):
        BINDINGS = [
            ("s", "set_default", "Set Default"),
            ("x", "download", "Download"),
        ]

        selected_id: Optional[str] = reactive(None)

        def compose(self) -> ComposeResult:  # type: ignore[override]
            with Vertical(id="left"):
                yield Label("Models (✅ downloaded)")
                lv = ListView(id="models_list")
                for m in models_cache:
                    row = _format_model_row(m)
                    item = ListItem(Label(row))
                    item.data = m  # attach model dict
                    lv.append(item)
                yield lv
            with Vertical(id="right"):
                yield Label("Details")
                yield Static("Select a model to see details.", id="details")
                yield Static("Press [s]=Set, [x]=Download", id="hints")

        def _get_current_model(self) -> Optional[Dict[str, Any]]:
            lv = self.query_one("#models_list", ListView)
            if lv.index is None or lv.index < 0 or lv.index >= len(lv.children):
                return None
            item = lv.children[lv.index]
            md = getattr(item, "data", None)
            return md if isinstance(md, dict) else None

        def _update_details(self) -> None:
            d = self._get_current_model()
            details = self.query_one("#details", Static)
            if not d:
                details.update("Select a model to see details.")
                self.selected_id = None
                return
            self.selected_id = str(d.get("id")) if d.get("id") else None
            lines = format_model_details(d)
            details.update("\n".join(lines))

        # Events for selection/highlight changes
        def on_list_view_selected(self, _event) -> None:  # type: ignore[override]
            self._update_details()

        def on_list_view_highlighted(self, _event) -> None:  # type: ignore[override]
            self._update_details()

        # Actions bound via BINDINGS
        def action_set_default(self) -> None:  # type: ignore[override]
            m = self._get_current_model()
            if not m:
                return
            model_id = m.get("id")
            if not model_id:
                return
            # Simple two-button confirm via in-place update
            right = self.query_one("#right")  # type: ignore
            try:
                cur = ctrl.set_default(model_id, scope="local")
                msg = f"Default set to {cur.get('id')} (local)."
            except Exception as e:  # pragma: no cover - interactive path
                msg = f"[red]Error:[/red] {e}"
            from textual.widgets import Static

            if not right.query("#op_msg"):
                right.mount(Static("", id="op_msg"))
            right.query_one("#op_msg", Static).update(msg)

        def action_download(self) -> None:  # type: ignore[override]
            m = self._get_current_model()
            if not m:
                return
            model_id = m.get("id")
            if not model_id:
                return
            right = self.query_one("#right")  # type: ignore
            try:
                path = ctrl.download(model_id)
                msg = f"Downloaded {model_id} → {path}"
            except Exception as e:  # pragma: no cover - interactive path
                msg = f"[red]Error:[/red] {e}"
            from textual.widgets import Static

            if not right.query("#op_msg"):
                right.mount(Static("", id="op_msg"))
            right.query_one("#op_msg", Static).update(msg)

    return ModelsView()
