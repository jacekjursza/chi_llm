"""Minimal Textual TUI launcher for chi_llm configuration.

This MVP provides a lightweight entry point that can be expanded with views.
It is intentionally small and imports Textual only within `launch_tui`.
"""

from typing import List, Optional


def launch_tui(
    ui_args: Optional[List[str]] = None,
) -> None:  # pragma: no cover - behavior tested via CLI mocks
    """Launch the Textual-based configuration UI.

    Parameters
    ----------
    ui_args : list[str] | None
        Optional passthrough arguments (currently unused in MVP).
    """
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
        ]

        def compose(self) -> ComposeResult:  # type: ignore[override]
            yield Header(show_clock=False)
            with Container(id="main"):
                yield ConfigHome()
            yield Footer()

        def action_show_models(self) -> None:  # type: ignore[override]
            # Lazy import to keep Textual deps scoped
            from textual.widgets import Static
            from .store import TUIStore
            from .views.models import build_models_text

            store = TUIStore()
            lines = build_models_text(store)
            text = "\n".join(["[b]Models[/b] (✅ downloaded)", ""] + lines)
            main = self.query_one("#main")  # type: ignore
            main.remove_children()
            main.mount(Static(text))

        def action_show_providers(self) -> None:  # type: ignore[override]
            from textual.widgets import Static
            from .store import TUIStore

            store = TUIStore()
            prov = store.get_provider()
            test = store.test_connection(prov)
            lines = [
                "[b]Provider[/b]",
                f"Type: {prov.get('type')}",
                f"Host: {prov.get('host')}:{prov.get('port')}",
                f"OK: {test.get('ok')} (models={test.get('models_count', 0)})",
            ]
            main = self.query_one("#main")  # type: ignore
            main.remove_children()
            main.mount(Static("\n".join(lines)))

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

    app = ChiLLMConfigApp()
    # Note: App.run() blocks; tests mock `launch_tui` from CLI to avoid running a TUI.
    app.run()
