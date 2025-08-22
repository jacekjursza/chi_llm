"""
LM Studio provider adapter.

Provides a minimal, synchronous client for LM Studio's OpenAI-compatible
HTTP API. No extra dependencies required; uses `requests` if available,
falls back to `urllib` otherwise.
"""

from __future__ import annotations

from typing import List, Dict, Optional, Any

import json


class LmStudioProvider:
    """
    Minimal LM Studio provider implementing the Provider protocol.

    Configuration:
    - host: str (default: 127.0.0.1)
    - port: int (default: 1234)
    - model: str (required by LM Studio for most requests)
    - timeout: float (seconds, default: 30)
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int | str = 1234,
        model: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.host = host or "127.0.0.1"
        self.port = port or 1234
        self.model = model
        self.timeout = timeout
        self.base_url = f"http://{self.host}:{self.port}/v1"

    # --- Basic HTTP helpers (requests optional) ---
    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            try:
                import requests  # type: ignore

                r = requests.post(url, json=payload, timeout=self.timeout)
                if r.status_code >= 400:
                    raise RuntimeError(
                        f"LM Studio error {r.status_code}: {r.text[:200]}"
                    )
                return r.json()
            except ModuleNotFoundError:
                # Fallback to stdlib
                from urllib import request, error

                data = json.dumps(payload).encode("utf-8")
                req = request.Request(
                    url, data=data, headers={"Content-Type": "application/json"}
                )
                try:
                    with request.urlopen(req, timeout=self.timeout) as resp:
                        body = resp.read().decode("utf-8")
                        return json.loads(body)
                except error.HTTPError as he:  # pragma: no cover - network dependent
                    msg = he.read().decode("utf-8")
                    raise RuntimeError(
                        f"LM Studio HTTP error {he.code}: {msg[:200]}"
                    ) from he
        except Exception as e:
            raise RuntimeError(
                (
                    f"Could not reach LM Studio at {self.base_url}. "
                    "Ensure the local server is running (Settings → Server) "
                    "and model is available. "
                    f"Error: {e}"
                )
            )

    # --- Provider protocol methods ---
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.model:
            raise RuntimeError("LM Studio provider requires 'model' in configuration.")
        payload = {
            "model": self.model,
            "prompt": prompt,
            # map common sampling params when present
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 256),
        }
        data = self._post("/completions", payload)
        # OpenAI-style completions: choices[0].text
        try:
            choice = data.get("choices", [{}])[0]
            text = choice.get("text")
            if text is None:
                # Some servers may return chat-like message for completions
                msg = choice.get("message", {})
                text = msg.get("content")
            return (text or "").strip()
        except Exception as e:
            raise RuntimeError(f"Unexpected LM Studio response: {e}")

    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        if not self.model:
            raise RuntimeError("LM Studio provider requires 'model' in configuration.")
        messages: List[Dict[str, str]] = []
        if history:
            for turn in history:
                if "user" in turn:
                    messages.append({"role": "user", "content": turn["user"]})
                if "assistant" in turn:
                    messages.append({"role": "assistant", "content": turn["assistant"]})
        messages.append({"role": "user", "content": message})

        payload = {"model": self.model, "messages": messages}
        data = self._post("/chat/completions", payload)
        try:
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})
            return (msg.get("content") or "").strip()
        except Exception as e:
            raise RuntimeError(f"Unexpected LM Studio response: {e}")

    def complete(self, text: str, **kwargs) -> str:
        # For LM Studio, use the same completions endpoint
        return self.generate(text, **kwargs)
