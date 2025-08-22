"""
Ollama provider adapter.

Minimal synchronous client for Ollama's local HTTP API.
Endpoints:
- POST /api/generate {model, prompt, stream=False}
- POST /api/chat {model, messages, stream=False}

No hard dependency on requests; falls back to urllib when missing.
"""

from __future__ import annotations

from typing import List, Dict, Optional, Any

import json


class OllamaProvider:
    """
    Minimal Ollama provider implementing the Provider protocol.

    Configuration:
    - host: str (default: 127.0.0.1)
    - port: int (default: 11434)
    - model: str (required)
    - timeout: float (seconds, default: 30)
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int | str = 11434,
        model: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.host = host or "127.0.0.1"
        self.port = port or 11434
        self.model = model
        self.timeout = timeout
        self.base_url = f"http://{self.host}:{self.port}"

    # --- Basic HTTP helpers (requests optional) ---
    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            try:
                import requests  # type: ignore

                r = requests.post(url, json=payload, timeout=self.timeout)
                if r.status_code >= 400:
                    raise RuntimeError(f"Ollama error {r.status_code}: {r.text[:200]}")
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
                        f"Ollama HTTP error {he.code}: {msg[:200]}"
                    ) from he
        except Exception as e:
            raise RuntimeError(
                (
                    f"Could not reach Ollama at {self.base_url}. "
                    "Ensure Ollama is running (e.g., `ollama serve`) and "
                    "the model is pulled. "
                    f"Error: {e}"
                )
            )

    # --- Provider protocol methods ---
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.model:
            raise RuntimeError("Ollama provider requires 'model' in configuration.")
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            # sampling params (best-effort mapping)
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
            },
        }
        data = self._post("/api/generate", payload)
        try:
            text = data.get("response")
            if text is None:
                # Some versions may return choices/message; handle gracefully
                choices = data.get("choices", [{}])
                text = choices[0].get("text") if choices else None
                if text is None:
                    msg = data.get("message", {})
                    text = msg.get("content")
            return (text or "").strip()
        except Exception as e:
            raise RuntimeError(f"Unexpected Ollama response: {e}")

    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        if not self.model:
            raise RuntimeError("Ollama provider requires 'model' in configuration.")
        messages: List[Dict[str, str]] = []
        if history:
            for turn in history:
                if "user" in turn:
                    messages.append({"role": "user", "content": turn["user"]})
                if "assistant" in turn:
                    messages.append({"role": "assistant", "content": turn["assistant"]})
        messages.append({"role": "user", "content": message})

        payload = {"model": self.model, "messages": messages, "stream": False}
        data = self._post("/api/chat", payload)
        try:
            msg = data.get("message", {})
            content = msg.get("content")
            if content is None:
                # Fallbacks
                choices = data.get("choices", [{}])
                if choices:
                    maybe = choices[0].get("message", {})
                    content = maybe.get("content")
            return (content or "").strip()
        except Exception as e:
            raise RuntimeError(f"Unexpected Ollama response: {e}")

    def complete(self, text: str, **kwargs) -> str:
        # Use generate for simple completion
        return self.generate(text, **kwargs)
