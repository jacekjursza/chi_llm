"""Headless TUI capture script (Textual).

Generates screenshots of key views and writes them under docs/.
Safe to run in CI; requires `pip install chi-llm[ui]` (Textual installed).
"""

from __future__ import annotations

import asyncio
from pathlib import Path


async def main() -> int:
    try:
        from chi_llm.tui.app import create_app
    except Exception as e:
        print(f"❌ Textual not available: {e}")
        print("Hint: pip install 'chi-llm[ui]'")
        return 1

    out_dir = Path(__file__).resolve().parents[1] / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)

    app = create_app()

    async with app.run_test(size=(120, 40)) as pilot:
        # Home
        path = app.save_screenshot("screen-home.png", path=str(out_dir))
        print("Saved:", path)

        # Models (config with local provider)
        await pilot.press("m")
        await pilot.pause(0.1)
        path = app.save_screenshot("screen-config-local.png", path=str(out_dir))
        print("Saved:", path)

        # Providers (external) + browse models (best-effort)
        await pilot.press("p")
        await pilot.pause(0.1)
        try:
            # Try to switch provider type programmatically via view method
            body = app.query_one("#config_body")
            cfg_view = body.parent  # ConfigView instance
            # Prefer ollama, fallback to lmstudio
            try:
                cfg_view._set_type("ollama")  # type: ignore[attr-defined]
            except Exception:
                cfg_view._set_type("lmstudio")  # type: ignore[attr-defined]
        except Exception:
            pass
        await pilot.pause(0.05)
        try:
            await pilot.click("#browse_models")
            await pilot.pause(0.2)
        except Exception:
            pass
        path = app.save_screenshot("screen-config-external.png", path=str(out_dir))
        print("Saved:", path)

        # Diagnostics
        await pilot.press("d")
        await pilot.pause(0.1)
        path = app.save_screenshot("screen-diagnostics.png", path=str(out_dir))
        print("Saved:", path)

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
