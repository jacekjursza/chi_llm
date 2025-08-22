"""Unified Config view for Models and Providers.

Shows provider selection at the top. When provider is "local", embeds the
Models view (list/filter/download, set default). For external providers
(lmstudio/ollama), shows a compact form with host/port/model, Test, and a
single "Build Config" button with scope toggle.
"""

from typing import Any, Dict, Optional


def create_config_view(store, initial_provider: Optional[str] = None) -> "object":
    from textual.app import ComposeResult
    from textual.containers import Vertical, VerticalScroll
    from textual.widgets import Label, Button, Static, Input
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
            # Provider selector row
            yield Static(f"Provider: {self.current_type}", id="provider_label")
            yield Button("Prev Type", id="type_prev")
            yield Button("Next Type", id="type_next")

            # Body switches based on provider
            with VerticalScroll(id="config_body"):
                yield Static("Loading…")

            # Actions footer (generic)
            yield Static("Scope: local", id="scope_label")
            yield Button("Toggle Scope", id="scope_toggle")
            yield Button("Test Connection", id="test_conn")
            yield Button("Build Config", id="build_config")
            yield Static("", id="status")

        def on_mount(self) -> None:  # type: ignore[override]
            self._render_body()

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

            # Update provider label
            self.query_one("#provider_label", Static).update(
                f"Provider: {self.current_type}"
            )

        def _cycle_type(self, direction: int) -> None:
            types = ["local", "lmstudio", "ollama"]
            try:
                idx = types.index(self.current_type)
            except ValueError:
                idx = 0
            self.current_type = types[(idx + direction) % len(types)]
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

            if event.button.id == "type_prev":
                self._cycle_type(-1)
                return
            if event.button.id == "type_next":
                self._cycle_type(1)
                return
            if event.button.id == "scope_toggle":
                self.scope = "global" if self.scope == "local" else "local"
                self.query_one("#scope_label", Static).update(f"Scope: {self.scope}")
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

    return ConfigView()
