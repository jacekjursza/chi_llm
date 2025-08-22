"""
OpenAI provider adapter.

Minimal synchronous client using the official OpenAI Python SDK when available.
Falls back to raising a helpful error if the SDK is not installed.

Configuration:
- api_key: str (required)
- model: str (required)
- base_url: str (optional; for custom endpoints). If not provided,
  tries to derive from `host` if it looks like a URL.
- timeout: float (optional, default 30s)
"""

from __future__ import annotations

from typing import Dict, List, Optional


class OpenAIProvider:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int | str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.model = (model or "").strip()
        self.timeout = timeout
        # Prefer explicit base_url; otherwise accept full URL passed in host
        if base_url:
            self.base_url = base_url
        elif host and (host.startswith("http://") or host.startswith("https://")):
            # Accept a direct base URL via host for convenience
            self.base_url = host
        else:
            self.base_url = None

        if not self.api_key:
            raise RuntimeError(
                "OpenAI provider requires an API key. Set CHI_LLM_PROVIDER_API_KEY "
                "or use 'chi-llm providers set openai --api-key ...'."
            )
        if not self.model:
            raise RuntimeError("OpenAI provider requires 'model' in configuration.")

        # Initialize SDK client lazily to allow tests to mock the module
        self._client = None

    # --- Internal: obtain a client instance ---
    def _client_openai(self):
        if self._client is not None:
            return self._client
        try:
            # New-style SDK (>=1.0)
            from openai import OpenAI  # type: ignore

            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            return self._client
        except Exception:
            # Old SDK fallback
            try:
                import openai as openai_sdk  # type: ignore

                openai_sdk.api_key = self.api_key
                if self.base_url:
                    openai_sdk.base_url = self.base_url  # type: ignore[attr-defined]
                self._client = openai_sdk
                return self._client
            except Exception as e:  # pragma: no cover - depends on env
                raise RuntimeError(
                    "OpenAI SDK not installed. Install with 'pip install openai' or "
                    "use 'chi-llm[full]' extras."
                ) from e

    # --- Provider protocol methods ---
    def generate(self, prompt: str, **kwargs) -> str:
        model = self.model
        client = self._client_openai()
        temperature = float(kwargs.get("temperature", 0.7))
        max_tokens = int(kwargs.get("max_tokens", 256))

        # Prefer chat completions for broad compatibility
        try:
            # New SDK
            if hasattr(client, "chat") and hasattr(client.chat, "completions"):
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                try:
                    return (resp.choices[0].message.content or "").strip()
                except Exception:
                    return ""
            # Old SDK
            if hasattr(client, "ChatCompletion"):
                resp = client.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return (resp["choices"][0]["message"]["content"] or "").strip()
        except Exception as e:
            raise RuntimeError(f"OpenAI generate() failed: {e}")
        return ""

    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        model = self.model
        client = self._client_openai()
        msgs: List[Dict[str, str]] = []
        if history:
            for turn in history:
                if "user" in turn:
                    msgs.append({"role": "user", "content": turn["user"]})
                if "assistant" in turn:
                    msgs.append({"role": "assistant", "content": turn["assistant"]})
        msgs.append({"role": "user", "content": message})
        try:
            if hasattr(client, "chat") and hasattr(client.chat, "completions"):
                resp = client.chat.completions.create(model=model, messages=msgs)
                try:
                    return (resp.choices[0].message.content or "").strip()
                except Exception:
                    return ""
            if hasattr(client, "ChatCompletion"):
                resp = client.ChatCompletion.create(model=model, messages=msgs)
                return (resp["choices"][0]["message"]["content"] or "").strip()
        except Exception as e:
            raise RuntimeError(f"OpenAI chat() failed: {e}")
        return ""

    def complete(self, text: str, **kwargs) -> str:
        # Simple alias to generate
        return self.generate(text, **kwargs)
