"""Models view helpers and controller for the Textual TUI.

This module is intentionally UI-framework agnostic to keep tests simple.
It exposes small utilities for formatting and a controller that bridges
user intents to the store layer (set default model, download model, etc.).
"""

from typing import List, Dict, Any, Optional


def _format_model_row(m: Dict[str, Any], current_id: Optional[str] = None) -> str:
    mark = "✅" if m.get("downloaded") else "  "
    star = "★" if current_id and m.get("id") == current_id else " "
    parts = [
        f"{mark}{star} {m.get('id')}",
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
    try:
        current_id = store.get_current_model().get("id")
    except Exception:
        current_id = None
    rows = [_format_model_row(m, current_id=current_id) for m in items]
    return rows


def format_model_details(
    m: Dict[str, Any], current_id: Optional[str] = None
) -> List[str]:
    """Return a detailed multi-line description of a model for display."""
    tags = ", ".join(m.get("tags") or [])
    is_default = bool(current_id and m.get("id") == current_id)
    return [
        f"ID: {m.get('id')}",
        f"Name: {m.get('name', '')}",
        f"Size: {m.get('size', '')} ({m.get('file_size_mb', '?')} MB)",
        f"Context: {m.get('context_window', '?')}",
        f"RAM (rec.): {m.get('recommended_ram_gb', '?')} GB",
        f"Tags: {tags}",
        f"Downloaded: {'yes' if m.get('downloaded') else 'no'}",
        f"Default: {'yes' if is_default else 'no'}",
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
    from textual.widgets import ListView, ListItem, Label, Static, Input
    from textual.reactive import reactive
    import threading
    import time

    ctrl = ModelsController(store)
    models_all: List[Dict[str, Any]] = ctrl.list()
    try:
        current_default_id: Optional[str] = store.get_current_model().get("id")
    except Exception:
        current_default_id = None

    class ModelsView(Horizontal):
        BINDINGS = [
            ("s", "set_default", "Set Default"),
            ("x", "download", "Download"),
            ("o", "toggle_sort", "Sort"),
            ("g", "toggle_downloaded_filter", "Downloaded Only"),
            ("v", "open_models_dir", "Open Dir"),
            ("f", "focus_filter", "Focus Filter"),
            ("l", "focus_list", "Focus List"),
        ]

        selected_id: Optional[str] = reactive(None)
        sort_mode: str = reactive("id")  # id | name | size | downloaded
        downloading_model_id: Optional[str] = reactive(None)
        filter_downloaded_only: bool = reactive(False)

        def compose(self) -> ComposeResult:  # type: ignore[override]
            with Vertical(id="left"):
                yield Label("Models (✅ downloaded)")
                yield Input(placeholder="Filter by id/name/tag", id="filter")
                # Build items first; ListView.append can't be used before mount
                list_items = []
                for m in models_all:
                    row = _format_model_row(m, current_id=current_default_id)
                    item = ListItem(Label(row))
                    item.data = m  # attach model dict
                    list_items.append(item)
                yield ListView(*list_items, id="models_list")
            with Vertical(id="right"):
                yield Label("Details")
                yield Static("Select a model to see details.", id="details")
                yield Label("Actions & Status")
                yield Static(
                    "[s]=Set, [x]=Download, [o]=Sort, [g]=Downloaded, "
                    "[v]=OpenDir, [l]=List, [f]=Filter",
                    id="hints",
                )
                yield Static("Sort: id", id="sort_label")
                yield Static("Downloaded only: off", id="filter_label")
                yield Static("Status: Idle", id="status_label")
                yield Static("", id="progress")
                yield Static("", id="op_msg")

        def on_mount(self) -> None:  # type: ignore[override]
            """Ensure the list has focus and an initial selection for arrow keys."""
            try:
                lv = self.query_one("#models_list")
                self.set_focus(lv)
                # Select first item if available
                if hasattr(lv, "children") and lv.children:
                    try:
                        lv.index = 0  # type: ignore[attr-defined]
                    except Exception:
                        pass
                self._update_details()
            except Exception:
                pass

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
            lines = format_model_details(d, current_id=current_default_id)
            details.update("\n".join(lines))

        # Events for selection/highlight changes
        def on_list_view_selected(self, _event) -> None:  # type: ignore[override]
            self._update_details()

        def on_list_view_highlighted(self, _event) -> None:  # type: ignore[override]
            self._update_details()

        def on_input_changed(self, _event) -> None:  # type: ignore[override]
            """Filter models list based on text input."""
            try:
                q = self.query_one("#filter", Input).value.strip().lower()
            except Exception:
                q = ""
            lv = self.query_one("#models_list", ListView)
            try:
                lv.clear()
            except Exception:
                # Fallback if ListView.clear not available
                for child in list(lv.children):
                    child.remove()

            def match(m: Dict[str, Any]) -> bool:
                if not q:
                    return True
                hay = " ".join(
                    [
                        str(m.get("id", "")),
                        str(m.get("name", "")),
                        " ".join(m.get("tags") or []),
                    ]
                ).lower()
                ok = q in hay
                if ok and self.filter_downloaded_only:
                    return bool(m.get("downloaded"))
                return (
                    ok if not self.filter_downloaded_only else bool(m.get("downloaded"))
                )

            # sorting helpers
            def sort_key(m: Dict[str, Any]):
                if self.sort_mode == "name":
                    return (str(m.get("name", "")), str(m.get("id", "")))
                if self.sort_mode == "size":
                    return (int(m.get("file_size_mb", 0)), str(m.get("id", "")))
                if self.sort_mode == "downloaded":
                    return (0 if m.get("downloaded") else 1, str(m.get("id", "")))
                return str(m.get("id", ""))

            filtered_sorted = sorted(filter(match, models_all), key=sort_key)
            for m in filtered_sorted:
                row = _format_model_row(m, current_id=current_default_id)
                item = ListItem(Label(row))
                item.data = m
                lv.append(item)
            self._update_details()

        def action_toggle_sort(self) -> None:  # type: ignore[override]
            order = ["id", "name", "size", "downloaded"]
            try:
                idx = order.index(self.sort_mode)
            except ValueError:
                idx = 0
            self.sort_mode = order[(idx + 1) % len(order)]
            # trigger rebuild using current filter value
            try:
                self.query_one("#sort_label", Static).update(f"Sort: {self.sort_mode}")
            except Exception:
                pass
            self.on_input_changed(None)  # type: ignore[arg-type]

        def action_focus_filter(self) -> None:  # type: ignore[override]
            try:
                self.set_focus(self.query_one("#filter"))
            except Exception:
                pass

        def action_focus_list(self) -> None:  # type: ignore[override]
            try:
                self.set_focus(self.query_one("#models_list"))
            except Exception:
                pass

        def action_toggle_downloaded_filter(self) -> None:  # type: ignore[override]
            self.filter_downloaded_only = not self.filter_downloaded_only
            try:
                self.query_one("#filter_label", Static).update(
                    f"Downloaded only: {'on' if self.filter_downloaded_only else 'off'}"
                )
            except Exception:
                pass
            self.on_input_changed(None)  # type: ignore[arg-type]

        # Actions bound via BINDINGS
        def action_set_default(self) -> None:  # type: ignore[override]
            m = self._get_current_model()
            if not m:
                return
            model_id = m.get("id")
            if not model_id:
                return
            # Prompt for scope (local/global) via modal
            from textual.widgets import Label, Button, Static
            from textual.screen import ModalScreen

            class ScopeScreen(ModalScreen[None]):
                def compose(self):  # type: ignore[override]
                    yield Label(f"Set default: {model_id}")
                    yield Button("Local", id="local")
                    yield Button("Global", id="global")
                    yield Button("Cancel", id="cancel")

                def on_button_pressed(self, event):  # type: ignore[override]
                    nonlocal current_default_id
                    right = self.app.query_one("#right")  # type: ignore
                    if event.button.id == "cancel":
                        self.app.pop_screen()
                        return
                    scope = "local" if event.button.id == "local" else "global"
                    try:
                        cur = ctrl.set_default(model_id, scope=scope)
                        current_default_id = cur.get("id")
                        msg = f"Default set to {cur.get('id')} ({scope})."
                        # refresh list labels with star
                        lv = self.app.query_one("#models_list")  # type: ignore
                        for item in lv.children:
                            md = getattr(item, "data", None)
                            if isinstance(md, dict):
                                row = _format_model_row(
                                    md, current_id=current_default_id
                                )
                                if item.children and hasattr(
                                    item.children[0], "update"
                                ):
                                    item.children[0].update(row)
                        # refresh details
                        self.app.query_one("#details", Static).update(
                            "\n".join(
                                format_model_details(m, current_id=current_default_id)
                            )
                        )
                    except Exception as e:  # pragma: no cover - interactive path
                        msg = f"[red]Error:[/red] {e}"
                    finally:
                        if not right.query("#op_msg"):
                            right.mount(Static("", id="op_msg"))
                        right.query_one("#op_msg", Static).update(msg)
                        self.app.pop_screen()

            self.app.push_screen(ScopeScreen())

        def action_download(self) -> None:  # type: ignore[override]
            m = self._get_current_model()
            if not m:
                return
            model_id = m.get("id")
            if not model_id:
                return
            # prevent parallel downloads
            if self.downloading_model_id:
                from textual.widgets import Static

                self.query_one("#status_label", Static).update(
                    f"Status: Downloading {self.downloading_model_id} (locked)"
                )
                self.query_one("#op_msg", Static).update(
                    f"Already downloading: {self.downloading_model_id}. Please wait."
                )
                return
            self.downloading_model_id = model_id
            right = self.query_one("#right")  # type: ignore
            from textual.widgets import Static

            right.query_one("#status_label", Static).update(
                f"Status: Downloading {model_id} (locked)"
            )
            right.query_one("#op_msg", Static).update(
                "Downloading... this may take a while"
            )
            # Start a progress loop (best-effort file size, fallback to pulse)
            progress_stop = threading.Event()

            expected_path = None
            target_bytes = 0
            try:
                expected_path = store.expected_model_path(model_id)
                mb = float(m.get("file_size_mb") or 0)
                target_bytes = int(mb * 1024 * 1024)
            except Exception:
                expected_path = None
                target_bytes = 0

            def _progress_loop():
                pos = 0
                prev_bytes = 0
                prev_t = time.monotonic()
                while not progress_stop.is_set():
                    text = None
                    if expected_path and target_bytes > 0 and expected_path.exists():
                        try:
                            size = expected_path.stat().st_size
                            pct = min(99, int(size * 100 / max(target_bytes, 1)))
                            bars = int(pct / 5)
                            # Best-effort ETA based on last interval
                            now = time.monotonic()
                            dt = max(1e-3, now - prev_t)
                            speed = max(0.0, (size - prev_bytes) / dt)
                            prev_bytes, prev_t = size, now
                            eta_txt = ""
                            if speed > 0:
                                rem = max(0, target_bytes - size)
                                eta_s = int(rem / speed)
                                m, s = divmod(eta_s, 60)
                                eta_txt = f" ETA ~ {m}m {s}s"
                            text = (
                                "Progress: ["
                                + "#" * bars
                                + " " * (20 - bars)
                                + f"] {pct}%"
                                + eta_txt
                            )
                        except Exception:
                            text = None
                    if text is None:
                        pos = (pos + 10) % 100
                        bars = int(pos / 5)
                        text = (
                            "Progress: [" + "#" * bars + " " * (20 - bars) + f"] {pos}%"
                        )

                    def _upd():
                        try:
                            right.query_one("#progress", Static).update(text)
                        except Exception:
                            pass

                    self.app.call_from_thread(_upd)
                    progress_stop.wait(2.0)

            threading.Thread(target=_progress_loop, daemon=True).start()

            def _worker():
                try:
                    path = ctrl.download(model_id)

                    def _ok():
                        # update flags and row
                        if isinstance(m, dict):
                            m["downloaded"] = True
                        try:
                            lv = self.query_one("#models_list")  # type: ignore
                            if lv.index is not None and 0 <= lv.index < len(
                                lv.children
                            ):
                                item = lv.children[lv.index]
                                if item.children:
                                    item.children[0].update(
                                        _format_model_row(
                                            m, current_id=current_default_id
                                        )
                                    )
                        except Exception:
                            pass
                        progress_stop.set()
                        right.query_one("#progress", Static).update("")
                        right.query_one("#op_msg", Static).update(
                            f"Downloaded {model_id} → {path}"
                        )
                        right.query_one("#status_label", Static).update("Status: Idle")
                        self.downloading_model_id = None

                    self.app.call_from_thread(_ok)
                except Exception as e:  # pragma: no cover - network dependent
                    e_msg = str(e)

                    def _err():
                        progress_stop.set()
                        right.query_one("#progress", Static).update("")
                        right.query_one("#op_msg", Static).update(
                            f"[red]Error:[/red] {e_msg}"
                        )
                        right.query_one("#status_label", Static).update("Status: Idle")
                        self.downloading_model_id = None

                    self.app.call_from_thread(_err)

            threading.Thread(target=_worker, daemon=True).start()

        def action_open_models_dir(self) -> None:  # type: ignore[override]
            from textual.widgets import Static
            import sys
            import os
            import subprocess

            try:
                p = store.get_models_dir()
                cmd_run = False
                try:
                    if sys.platform.startswith("darwin"):
                        subprocess.Popen(["open", str(p)])
                        cmd_run = True
                    elif os.name == "nt":
                        subprocess.Popen(["explorer", str(p)])
                        cmd_run = True
                    else:
                        subprocess.Popen(["xdg-open", str(p)])
                        cmd_run = True
                except Exception:
                    cmd_run = False
                self.query_one("#op_msg", Static).update(
                    f"Opened models directory: {p}" if cmd_run else f"Models dir: {p}"
                )
            except Exception as e:
                self.query_one("#op_msg", Static).update(f"[red]Error:[/red] {e}")

    return ModelsView()
