"""
OpenAI CLI provider adapter.

Invokes the locally authenticated `openai` CLI as a subprocess and
returns stdout as the model response. This allows using the vendor CLI
without managing API keys inside this library.

Configuration keys (provider section):
- type: "openai-cli"
- model: optional model id (often required by the CLI)
- binary: optional binary name/path (default: "openai")
- timeout: optional seconds (default: 30)
- args: optional extra CLI args (list of strings)

Notes:
- We do not enforce a particular subcommand; by default, we pipe the
  prompt to the CLI and rely on user-provided defaults/aliases. For most
  setups, consider passing suitable `args`, e.g.:
  ["chat.completions.create", "-m", "gpt-4o-mini", "-g", "user"]
  In absence of args, we pass only `-m <model>` when available.
"""

from __future__ import annotations

from typing import List, Dict, Optional
import shutil
import subprocess


class OpenAICLIProvider:
    def __init__(
        self,
        model: Optional[str] = None,
        binary: str = "openai",
        timeout: float = 30.0,
        args: Optional[List[str]] = None,
    ) -> None:
        self.model = model
        self.binary = binary or "openai"
        self.timeout = timeout
        self.args = list(args or [])

        if shutil.which(self.binary) is None:
            raise RuntimeError(
                "OpenAI CLI not found in PATH. Install and run 'openai login'."
            )

    def _run(self, text: str) -> str:
        cmd: List[str] = [self.binary]
        if self.args:
            cmd += self.args
        elif self.model:
            # Minimal attempt to pass model; exact subcommand depends on user env
            cmd += ["-m", str(self.model)]
        try:
            proc = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                check=False,
            )
        except FileNotFoundError as e:  # pragma: no cover
            raise RuntimeError("OpenAI CLI not found in PATH.") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(
                f"OpenAI CLI timed out after {self.timeout} seconds"
            ) from e

        if proc.returncode != 0:
            err = (proc.stderr.decode("utf-8", errors="ignore") or "").strip()
            raise RuntimeError(f"OpenAI CLI error: {err[:200]}")
        out = (proc.stdout.decode("utf-8", errors="ignore") or "").strip()
        return out

    def generate(self, prompt: str, **kwargs) -> str:
        return self._run(prompt)

    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        parts: List[str] = []
        if history:
            for turn in history:
                if "user" in turn:
                    parts.append(f"User: {turn['user']}")
                if "assistant" in turn:
                    parts.append(f"Assistant: {turn['assistant']}")
        parts.append(f"User: {message}\nAssistant:")
        text = "\n".join(parts)
        return self._run(text)

    def complete(self, text: str, **kwargs) -> str:
        return self._run(text)
