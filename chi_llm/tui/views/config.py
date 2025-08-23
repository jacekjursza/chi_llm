"""Unified Config view for Models and Providers.

Shows provider selection at the top. When provider is "local", embeds the
Models view (list/filter/download, set default). For external providers
(lmstudio/ollama), shows a compact form with host/port/model, Test, and a
single "Build Config" button with scope toggle.
"""

from typing import Any, Dict, Optional


def create_config_view(store, initial_provider: Optional[str] = None) -> "object":
    from textual.app import ComposeResult
    from textual.containers import Vertical, VerticalScroll, Horizontal
    from textual.widgets import (
        Label,
        Button,
        Static,
        Input,
        Select,
        ListView,
        ListItem,
    )
    from textual.reactive import reactive

    from .models import create_models_view
    from .providers import ProvidersController

    ctrl = ProvidersController(store)
    initial = ctrl.get()
    provider_type = (initial_provider or initial.get("type") or "local").strip()

    class ConfigView(Vertical):
        current_type: str = reactive(provider_type)
        scope: str = reactive("local")  # local | global

        def compose(self) -> ComposeResult:  # type: ignore[override]
            yield Label("Configuration")
            # Provider selector row (dropdown)
            yield Static("Provider:")
            yield Select(
                options=[
                    ("Local", "local"),
                    ("LM Studio", "lmstudio"),
                    ("Ollama", "ollama"),
                ],
                value=self.current_type,
                id="provider_select",
            )

            # Actions row (compact) pinned above the body so it stays visible
            with Horizontal(id="actions_row"):
                yield Static("Scope: local", id="scope_label")
                yield Button("Toggle Scope", id="scope_toggle")
                yield Button("Test Connection", id="test_conn")
                yield Button("Build Config", id="build_config")
                yield Button("Back", id="back")
            yield Static("", id="status")

            # Body switches based on provider
            with VerticalScroll(id="config_body"):
                yield Static("Loading…")

        def on_mount(self) -> None:  # type: ignore[override]
            self._render_body()

        # Handle provider select changes
        def on_select_changed(self, event) -> None:  # type: ignore[override]
            try:
                v = getattr(event, "value", None)
            except Exception:
                v = None
            if isinstance(v, str):
                self._set_type(v)

        def _render_body(self) -> None:
            body = self.query_one("#config_body")
            # clear
            try:
                body.clear()
            except Exception:
                for child in list(body.children):
                    child.remove()

            if self.current_type == "local":
                # Embed Models view for local (llama.cpp) provider
                try:
                    body.mount(create_models_view(store))
                except Exception:
                    body.mount(Static("Failed to load Models view."))
            else:
                # Compact form for external providers
                prov = ctrl.get()
                host = str(prov.get("host") or "127.0.0.1")
                port = str(prov.get("port") or "")
                model = str(prov.get("model") or "")

                body.mount(Label(f"{self.current_type.upper()} Settings"))
                body.mount(Label("Host"))
                body.mount(Input(value=host, placeholder="127.0.0.1", id="host"))
                body.mount(Label("Port"))
                body.mount(Input(value=port, placeholder="11434", id="port"))
                body.mount(Label("Model (optional)"))
                body.mount(Input(value=model, placeholder="model-id", id="model"))
                # Model browser controls
                body.mount(Button("Browse Models", id="browse_models"))
                body.mount(Static("", id="models_status"))
                body.mount(ListView(id="models_list"))

            # No label update needed; Select displays current value

        def _set_type(self, typ: str) -> None:
            if typ in ("local", "lmstudio", "ollama"):
                self.current_type = typ
                self._render_body()

        def _read_form(self) -> Dict[str, Any]:
            # Only for external providers
            if self.current_type == "local":
                return {"type": "local"}
            host = "127.0.0.1"
            port = None
            model = None
            try:
                host = self.query_one("#host", Input).value.strip() or host
            except Exception:
                pass
            try:
                port_txt = self.query_one("#port", Input).value.strip()
                port = int(port_txt) if port_txt else None
            except Exception:
                port = None
            try:
                mv = self.query_one("#model", Input).value.strip()
                model = mv or None
            except Exception:
                model = None
            return {
                "type": self.current_type,
                "host": host,
                "port": port,
                "model": model,
            }

        def on_button_pressed(self, event) -> None:  # type: ignore[override]
            from textual.widgets import Static

            if event.button.id == "scope_toggle":
                self.scope = "global" if self.scope == "local" else "local"
                self.query_one("#scope_label", Static).update(f"Scope: {self.scope}")
                return
            if event.button.id == "back":
                # Navigate back to home (do not depend on app-local classes)
                try:
                    from textual.widgets import Static as _Static

                    main = self.app.query_one("#main")  # type: ignore
                    main.remove_children()
                    main.mount(
                        _Static("Back to home. Press m/p/d to open respective views.")
                    )
                except Exception:
                    pass
                return
            if event.button.id == "test_conn":
                if self.current_type == "local":
                    self.query_one("#status", Static).update(
                        "Local provider requires no connection."
                    )
                    return
                prov = self._read_form()
                res = ctrl.test(prov)
                self.query_one("#status", Static).update(
                    f"OK: {res.get('ok')} (models={res.get('models_count',0)})"
                )
                return
            if event.button.id == "build_config":
                prov = self._read_form()
                out = ctrl.set(self.scope, prov)
                self.query_one("#status", Static).update(
                    f"Config saved to {self.scope}. Type={out.get('type')}"
                )
                return
            if event.button.id == "browse_models":
                if self.current_type == "local":
                    self.query_one("#models_status", Static).update(
                        "Local provider has no remote models to list."
                    )
                    return
                prov = self._read_form()
                try:
                    items = ctrl.list_models(prov)
                except Exception:
                    items = []
                # Populate the list view
                try:
                    lv = self.query_one("#models_list", ListView)
                    lv.clear()
                except Exception:
                    lv = None
                count = 0
                if items and lv is not None:
                    for m in items:
                        label = f"{m.get('id')}  {m.get('size','') or ''}".strip()
                        it = ListItem(Label(label))
                        it.data = m
                        lv.append(it)
                        count += 1
                self.query_one("#models_status", Static).update(
                    f"Models: {count} found" if count else "No models found."
                )
                return

        # Update model field when user selects a model from the list
        def on_list_view_selected(self, event) -> None:  # type: ignore[override]
            try:
                if (
                    getattr(getattr(event, "list_view", None), "id", "")
                    != "models_list"
                ):
                    return
                lv = self.query_one("#models_list", ListView)
                if lv.index is None or lv.index < 0 or lv.index >= len(lv.children):
                    return
                item = lv.children[lv.index]
                md = getattr(item, "data", None)
                if isinstance(md, dict) and md.get("id"):
                    self.query_one("#model", Input).value = str(md.get("id"))
                    self.query_one("#status", Static).update(
                        f"Selected model: {md.get('id')}"
                    )
            except Exception:
                pass

    return ConfigView()
