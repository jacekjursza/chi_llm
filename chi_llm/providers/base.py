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
