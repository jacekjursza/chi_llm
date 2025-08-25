from typing import Protocol, List, Dict, Optional


class Provider(Protocol):
    """
    Minimal synchronous provider interface for text generation backends.

    Implementations should be lightweight and focused. Async support,
    streaming, and advanced features can be added incrementally without
    breaking this minimal contract.
    """

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        ...

    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """Chat with optional conversation history."""
        ...

    def complete(self, text: str, **kwargs) -> str:
        """Complete/continue the given text."""
        ...

    # Optional capability: list available models for this provider type.
    # Implementations may require specific kwargs (e.g., host/port for local servers,
    # api_key/base_url for external APIs). Returns a list of model IDs.
    @classmethod
    def discover_models(cls, **kwargs) -> List[str]:  # pragma: no cover - optional
        ...
