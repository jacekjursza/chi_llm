"""
Claude CLI provider adapter.

Invokes the locally authenticated `claude` CLI as a subprocess and
returns its stdout as the model response. This enables using the
Anthropic CLI as a provider without handling API keys in this library.

Configuration keys (provider section):
- type: "claude-cli"
- model: optional model id (passed via -m)
- binary: optional binary name/path (default: "claude")
- timeout: optional seconds (default: 30)
- args: optional extra CLI args (list of strings)

Notes:
- If the CLI is missing, a helpful error message is raised.
- Chat is implemented by flattening history into a single prompt.
"""

from __future__ import annotations

from typing import List, Dict, Optional
import shutil
import subprocess


class ClaudeCLIProvider:
    def __init__(
        self,
        model: Optional[str] = None,
        binary: str = "claude",
        timeout: float = 30.0,
        args: Optional[List[str]] = None,
    ) -> None:
        self.model = model
        self.binary = binary or "claude"
        self.timeout = timeout
        self.args = list(args or [])

        # Validate binary presence early for clearer errors
        if shutil.which(self.binary) is None:
            raise RuntimeError(
                "Claude CLI not found in PATH. Install: https://github.com/anthropics/anthropic-cli"
            )

    def _run(self, text: str) -> str:
        cmd: List[str] = [self.binary]
        if self.model:
            cmd += ["-m", str(self.model)]
        if self.args:
            cmd += self.args
        try:
            proc = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                check=False,
            )
        except FileNotFoundError as e:  # pragma: no cover - which above should handle
            raise RuntimeError(
                "Claude CLI not found in PATH. Install anthropic CLI."
            ) from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(
                f"Claude CLI timed out after {self.timeout} seconds"
            ) from e

        if proc.returncode != 0:
            err = (proc.stderr.decode("utf-8", errors="ignore") or "").strip()
            raise RuntimeError(f"Claude CLI error: {err[:200]}")
        out = (proc.stdout.decode("utf-8", errors="ignore") or "").strip()
        return out

    # --- Provider protocol methods ---
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
