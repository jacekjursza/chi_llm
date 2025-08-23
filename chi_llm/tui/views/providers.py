"""Providers view helpers and controller for the Textual TUI.

Lets the user switch provider (local / lmstudio / ollama), edit connection
fields, test connectivity, and persist the config via a clear "Build config"
action (local or global scope).
"""

from typing import Any, Dict, Optional


class ProvidersController:
    def __init__(self, store) -> None:
        self.store = store

    def get(self) -> Dict[str, Any]:
        return self.store.get_provider()

    def set(self, scope: str, provider: Dict[str, Any]) -> Dict[str, Any]:
        return self.store.set_provider(scope, provider)

    def test(self, provider: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.store.test_connection(provider)

    def list_models(self, provider: Optional[Dict[str, Any]] = None):
        return self.store.list_provider_models(provider)


def create_providers_view(store) -> "object":
    """Create an interactive Providers view bound to the store.

    Includes fields for provider type, host, port, model, and actions to test
    connection and build (persist) the configuration (local/global).
    """
    from textual.app import ComposeResult
    from textual.containers import Vertical
    from textual.widgets import Label, Input, Button, Static
    from textual.reactive import reactive

    ctrl = ProvidersController(store)
    initial = ctrl.get()

    class ProvidersView(Vertical):
        # Simple cycling through supported types via a button
        supported_types = ("local", "lmstudio", "ollama")
        scope: str = reactive("local")  # local | global

        def compose(self) -> ComposeResult:  # type: ignore[override]
            prov_type = str(initial.get("type") or "local")
            host = str(initial.get("host") or "127.0.0.1")
            port = str(initial.get("port") or "")
            model = str(initial.get("model") or "")

            yield Label("Provider Configuration")
            yield Static(
                """Use the fields below to configure provider.
Supported: local / lmstudio / ollama. Test, then Build config."""
            )

            yield Label(f"Type: {prov_type}", id="type_label")
            yield Button("Change Type", id="type_change")

            yield Label("Host")
            yield Input(value=host, placeholder="127.0.0.1", id="host")
            yield Label("Port")
            yield Input(value=port, placeholder="11434", id="port")
            yield Label("Model (optional)")
            yield Input(value=model, placeholder="qwen2.5-coder-0.5b", id="model")

            yield Label("Actions")
            yield Button("Test Connection", id="test")
            yield Button("Build Local Config", id="build_local")
            yield Button("Build Global Config", id="build_global")
            yield Button("Back", id="back")

            yield Static("Scope: local", id="scope_label")
            yield Static("", id="status")

        def _current_provider(self) -> Dict[str, Any]:
            # Read current UI values
            from textual.widgets import Input

            lab = self.query_one("#type_label", Label)
            rend = getattr(lab, "renderable", "")
            txt = str(getattr(rend, "plain", rend))
            typ = txt.replace("Type: ", "")
            host = self.query_one("#host", Input).value.strip() or "127.0.0.1"
            port_txt = self.query_one("#port", Input).value.strip()
            try:
                port = int(port_txt) if port_txt else None
            except Exception:
                port = None
            model = self.query_one("#model", Input).value.strip() or None
            return {"type": typ, "host": host, "port": port, "model": model}

        def on_button_pressed(self, event) -> None:  # type: ignore[override]
            from textual.widgets import Static, Label

            if event.button.id == "type_change":
                # Cycle to next type
                lab = self.query_one("#type_label", Label)
                rend = getattr(lab, "renderable", "")
                txt = str(getattr(rend, "plain", rend))
                cur = txt.replace("Type: ", "")
                try:
                    idx = self.supported_types.index(cur)
                except ValueError:
                    idx = 0
                nxt = self.supported_types[(idx + 1) % len(self.supported_types)]
                self.query_one("#type_label", Label).update(f"Type: {nxt}")
                self.query_one("#status", Static).update(
                    f"Switched type to {nxt}. Adjust host/port if needed."
                )
                return

            if event.button.id == "test":
                prov = self._current_provider()
                res = ctrl.test(prov)
                ok = res.get("ok")
                msg = (
                    f"OK: {ok} (models={res.get('models_count',0)})"
                    if prov["type"] != "local"
                    else "Local provider requires no connection."
                )
                self.query_one("#status", Static).update(msg)
                return

            if event.button.id in ("build_local", "build_global"):
                scope = "local" if event.button.id == "build_local" else "global"
                self.query_one("#scope_label", Static).update(f"Scope: {scope}")
                prov = self._current_provider()
                out = ctrl.set(scope, prov)
                self.query_one("#status", Static).update(
                    f"Config saved to {scope}. Type={out.get('type')}"
                )
                return

            if event.button.id == "back":
                # Navigate back to home
                try:
                    from textual.widgets import Static as _Static

                    main = self.app.query_one("#main")  # type: ignore
                    main.remove_children()
                    main.mount(
                        _Static("Back to home. Press m/p/d to open respective views.")
                    )
                except Exception:
                    pass

    return ProvidersView()
