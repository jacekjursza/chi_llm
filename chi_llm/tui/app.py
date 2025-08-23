"""Minimal Textual TUI launcher for chi_llm configuration.

This MVP provides a lightweight entry point that can be expanded with views.
It is intentionally small and imports Textual only within `launch_tui`.
"""

from typing import List, Optional


def create_app():
    """Create the Textual App instance for headless testing or running."""
    try:
        # Import Textual only when launching UI to keep it optional.
        from textual.app import App, ComposeResult
        from textual.widgets import Header, Footer, Static
        from textual.containers import Container
    except Exception as e:  # Surface a clear error if Textual is missing/broken
        raise RuntimeError(
            "Textual is not available. Install with: pip install 'chi-llm[ui]'"
        ) from e

    class ConfigHome(Static):
        """Simple home placeholder for MVP."""

        def on_mount(self) -> None:  # type: ignore[override]
            self.update(
                """
[b]chi_llm Configuration[/b]\n
This is the new Textual-based TUI (MVP).

- Press Q to quit.
- Models, Providers, Diagnostics, and Bootstrap views will be added next.
""".strip()
            )

    class ChiLLMConfigApp(App):
        CSS = """
        Screen { padding: 1 2; }
        #main { height: 100%; }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("m", "show_models", "Models"),
            ("p", "show_providers", "Providers"),
            ("d", "show_diagnostics", "Diagnostics"),
            ("e", "export_diagnostics", "Export Diag"),
            ("s", "set_default_model", "Set Model"),
            ("x", "download_model", "Download"),
        ]

        def compose(self) -> ComposeResult:  # type: ignore[override]
            yield Header(show_clock=False)
            with Container(id="main"):
                yield ConfigHome()
            yield Footer()

        def action_show_models(self) -> None:  # type: ignore[override]
            # Lazy import to keep Textual deps scoped
            from .store import TUIStore
            from .views.config import create_config_view

            store = TUIStore()
            # Open unified config with provider preselected to local
            view = create_config_view(store, initial_provider="local")
            main = self.query_one("#main")  # type: ignore
            main.remove_children()
            main.mount(view)

        def action_show_providers(self) -> None:  # type: ignore[override]
            from .store import TUIStore
            from .views.config import create_config_view

            store = TUIStore()
            view = create_config_view(store)
            main = self.query_one("#main")  # type: ignore
            main.remove_children()
            main.mount(view)

        def action_show_diagnostics(self) -> None:  # type: ignore[override]
            from textual.widgets import Static
            from .store import TUIStore

            store = TUIStore()
            d = store.get_diagnostics()
            py = d.get("python", {})
            node = d.get("node", {})
            cache = d.get("cache", {})
            model = d.get("model", {})
            net = d.get("network", {})
            lines = ["[b]Diagnostics[/b]"]
            lines.append(
                f"Python: {py.get('version','?')} ({py.get('implementation','?')})"
            )
            lines.append(f"Node: {'ok' if node.get('ok') else 'missing'}")
            lines.append(
                "Cache: "
                f"{cache.get('path','?')} "
                f"exists={cache.get('exists')} "
                f"writable={cache.get('writable')}"
            )
            lines.append(
                "Model: "
                f"{model.get('current','?')} "
                f"fits={'yes' if model.get('fits') else 'no'}"
            )
            lines.append(f"Network(HF): {'ok' if net.get('ok') else 'fail'}")
            main = self.query_one("#main")  # type: ignore
            main.remove_children()
            main.mount(Static("\n".join(lines)))

        def action_export_diagnostics(self) -> None:  # type: ignore[override]
            from textual.widgets import Static
            from .store import TUIStore
            from pathlib import Path as _Path

            store = TUIStore()
            out = store.export_diagnostics(_Path.cwd() / "chi_llm_diagnostics.json")
            main = self.query_one("#main")  # type: ignore
            main.remove_children()
            main.mount(Static(f"Diagnostics exported to: {out}"))

        # ----- Models interactive actions -----
        def action_set_default_model(self) -> None:  # type: ignore[override]
            """Prompt for model id and set as default (local/global)."""
            from textual.widgets import Label, Input, Button
            from textual.screen import ModalScreen
            from .store import TUIStore

            store = TUIStore()

            class SetModelScreen(ModalScreen[None]):
                def compose(self):  # type: ignore[override]
                    yield Label("Set default model")
                    yield Label("Model ID:")
                    yield Input(placeholder="e.g. phi3-mini", id="model_id")
                    yield Label("Scope:")
                    yield Button("Set Local", id="set_local")
                    yield Button("Set Global", id="set_global")
                    yield Button("Cancel", id="cancel")

                def on_button_pressed(self, event):  # type: ignore[override]
                    from textual.widgets import Input

                    model_id = self.query_one("#model_id", Input).value.strip()
                    if event.button.id == "cancel":
                        self.app.pop_screen()
                        return
                    scope = "local" if event.button.id == "set_local" else "global"
                    main = self.app.query_one("#main")  # type: ignore
                    try:
                        from .views.models import ModelsController

                        ctrl = ModelsController(store)
                        cur = ctrl.set_default(model_id, scope=scope)
                        msg = f"Default model set to {cur.get('id')} (scope={scope})."
                        from textual.widgets import Static

                        main.remove_children()
                        main.mount(Static(msg))
                    except Exception as e:  # pragma: no cover - interactive path
                        from textual.widgets import Static

                        main.remove_children()
                        main.mount(Static(f"[red]Error:[/red] {e}"))
                    finally:
                        self.app.pop_screen()

            self.push_screen(SetModelScreen())

        def action_download_model(self) -> None:  # type: ignore[override]
            """Prompt for model id and trigger download via store."""
            from textual.widgets import Label, Input, Button
            from textual.screen import ModalScreen
            from .store import TUIStore

            store = TUIStore()

            class DownloadScreen(ModalScreen[None]):
                def compose(self):  # type: ignore[override]
                    yield Label("Download model")
                    yield Label("Model ID:")
                    yield Input(placeholder="e.g. phi3-mini", id="model_id")
                    yield Button("Download", id="download")
                    yield Button("Cancel", id="cancel")

                def on_button_pressed(self, event):  # type: ignore[override]
                    from textual.widgets import Input

                    model_id = self.query_one("#model_id", Input).value.strip()
                    if event.button.id == "cancel":
                        self.app.pop_screen()
                        return
                    main = self.app.query_one("#main")  # type: ignore
                    try:
                        from .views.models import ModelsController

                        ctrl = ModelsController(store)
                        path = ctrl.download(model_id)
                        msg = f"Model '{model_id}' downloaded to: {path}"
                        from textual.widgets import Static

                        main.remove_children()
                        main.mount(Static(msg))
                    except Exception as e:  # pragma: no cover - interactive path
                        from textual.widgets import Static

                        main.remove_children()
                        main.mount(Static(f"[red]Error:[/red] {e}"))
                    finally:
                        self.app.pop_screen()

            self.push_screen(DownloadScreen())

    return ChiLLMConfigApp()


def launch_tui(
    ui_args: Optional[List[str]] = None,
) -> None:  # pragma: no cover - behavior tested via CLI mocks
    """Launch the Textual-based configuration UI."""
    app = create_app()
    # Note: App.run() blocks; tests mock `launch_tui` from CLI to avoid running a TUI.
    app.run()
