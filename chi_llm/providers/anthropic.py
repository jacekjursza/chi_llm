"""
Anthropic provider adapter.

Minimal synchronous wrapper around the official Anthropic SDK.
Implements generate/chat/complete using Messages API.

Configuration:
- api_key: str (required)
- model: str (required), e.g., "claude-3-haiku-20240307"
- timeout: float (optional)
"""

from __future__ import annotations

from typing import Dict, List, Optional


class AnthropicProvider:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.model = (model or "").strip()
        self.timeout = timeout
        if not self.api_key:
            raise RuntimeError(
                "Anthropic provider requires an API key. Set CHI_LLM_PROVIDER_API_KEY "
                "or use 'chi-llm providers set anthropic --api-key ...'."
            )
        if not self.model:
            raise RuntimeError("Anthropic provider requires 'model' in configuration.")

        self._client = None

    # --- internal: SDK client ---
    def _client_anthropic(self):
        if self._client is not None:
            return self._client
        try:
            import anthropic  # type: ignore

            # SDK v0.30+: instantiate client with api_key
            self._client = anthropic.Anthropic(api_key=self.api_key)
            return self._client
        except Exception as e:  # pragma: no cover - depends on env
            raise RuntimeError(
                "Anthropic SDK not installed. Install with 'pip install anthropic' or "
                "use 'chi-llm[full]' extras."
            ) from e

    # --- helpers ---
    @staticmethod
    def _extract_text_from_message_resp(resp) -> str:
        # Anthropic messages.create returns object with .content: list[ContentBlock]
        try:
            parts = getattr(resp, "content", None)
            if isinstance(parts, list) and parts:
                # Prefer .text when available
                texts = []
                for part in parts:
                    if hasattr(part, "text") and isinstance(part.text, str):
                        texts.append(part.text)
                    elif isinstance(part, dict) and isinstance(part.get("text"), str):
                        texts.append(part.get("text", ""))
                if texts:
                    return "".join(texts).strip()
            # Fallbacks
            if hasattr(resp, "text") and isinstance(resp.text, str):
                return resp.text.strip()
        except Exception:
            pass
        return ""

    # --- Provider protocol methods ---
    def generate(self, prompt: str, **kwargs) -> str:
        client = self._client_anthropic()
        temperature = float(kwargs.get("temperature", 0.7))
        max_tokens = int(kwargs.get("max_tokens", 256))
        try:
            # Messages API
            resp = client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return self._extract_text_from_message_resp(resp)
        except Exception as e:
            raise RuntimeError(f"Anthropic generate() failed: {e}")

    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        client = self._client_anthropic()
        messages: List[Dict[str, str]] = []
        if history:
            for turn in history:
                if "user" in turn:
                    messages.append({"role": "user", "content": turn["user"]})
                if "assistant" in turn:
                    messages.append({"role": "assistant", "content": turn["assistant"]})
        messages.append({"role": "user", "content": message})

        try:
            resp = client.messages.create(
                model=self.model, messages=messages, max_tokens=256
            )
            return self._extract_text_from_message_resp(resp)
        except Exception as e:
            raise RuntimeError(f"Anthropic chat() failed: {e}")

    def complete(self, text: str, **kwargs) -> str:
        # Alias to generate for simple completions
        return self.generate(text, **kwargs)

    # --- Discovery ---
    @classmethod
    def discover_models(
        cls,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 5.0,
    ) -> List[str]:  # pragma: no cover - network dependent
        key = (api_key or "").strip()
        if not key:
            raise RuntimeError("Anthropic discover requires api_key")
        base = (base_url or "https://api.anthropic.com").rstrip("/")
        url = f"{base}/v1/models"
        try:
            try:
                import requests  # type: ignore

                headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
                r = requests.get(url, headers=headers, timeout=timeout)
                r.raise_for_status()
                data = r.json()
            except ModuleNotFoundError:
                from urllib import request, error
                import json as _json

                req = request.Request(url)
                req.add_header("x-api-key", key)
                req.add_header("anthropic-version", "2023-06-01")
                try:
                    with request.urlopen(req, timeout=timeout) as resp:
                        data = _json.loads(resp.read().decode("utf-8"))
                except error.HTTPError as he:
                    raise RuntimeError(f"HTTP {he.code}") from he
        except Exception as e:
            raise RuntimeError(f"Anthropic discover failed: {e}")
        items: List[str] = []
        arr = data.get("data") or data.get("models") or []
        for it in arr:
            mid = it.get("id") or it.get("name")
            if isinstance(mid, str) and mid:
                items.append(mid)
        return items
