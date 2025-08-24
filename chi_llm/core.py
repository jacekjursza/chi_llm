"""Core module for chi_llm (micro-LLM)."""

import os
import warnings
from pathlib import Path
from typing import Optional, Dict, List
from threading import Lock
from llama_cpp import Llama
from .utils import load_config
from huggingface_hub import hf_hub_download

# Suppress llama.cpp warnings
warnings.filterwarnings("ignore")
os.environ["LLAMA_CPP_LOG_LEVEL"] = "ERROR"

# Import model management
try:
    from .models import ModelManager, MODELS

    HAS_MODEL_MANAGER = True
except ImportError:
    HAS_MODEL_MANAGER = False

# Legacy model configuration (fallback)
MODEL_REPO = "lmstudio-community/gemma-3-270m-it-GGUF"
MODEL_FILE = "gemma-3-270m-it-Q4_K_M.gguf"
MODEL_DIR = Path.home() / ".cache" / "chi_llm"

# Singleton pattern for model management
_model_instance = None
_model_lock = Lock()
_generation_lock = Lock()  # Protect model inference calls


class MicroLLM:
    """Zero‑config micro LLM with optional providers/router."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        model_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        verbose: bool = False,
    ):
        """Initialize with optional model id/path and tuning params."""
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.verbose = verbose
        self.model_path = model_path
        self.model_id = model_id
        # Provider-aware initialization (non-breaking):
        # Loads optional provider config, but default behavior remains
        # local llama.cpp unless an external provider is explicitly set.
        self.provider_config: Dict[str, object] = {}
        self._provider = None  # External provider instance when configured
        self._provider_type: Optional[str] = None
        self._provider_error: Optional[str] = None
        self._router = None  # Multi-provider router when configured
        self.tags: Optional[List[str]] = None
        provider_local_model: Optional[str] = None
        provider_local_model_path: Optional[str] = None
        try:
            cfg = load_config()
            provider = cfg.get("provider") if isinstance(cfg, dict) else None
            profiles = cfg.get("provider_profiles") if isinstance(cfg, dict) else None
            # Initialize router if profiles are defined
            if isinstance(profiles, list) and profiles:
                try:
                    from .providers.router import ProviderRouter

                    self._router = ProviderRouter(profiles)
                except Exception:
                    self._router = None
            if isinstance(provider, dict) and provider.get("type"):
                self.provider_config = provider
                # Capture local provider model as a fallback only
                if provider.get("type") == "local":
                    prov_model = provider.get("model")
                    if isinstance(prov_model, str) and prov_model:
                        provider_local_model = prov_model
                    prov_model_path = provider.get("model_path")
                    if isinstance(prov_model_path, str) and prov_model_path:
                        provider_local_model_path = prov_model_path
                elif provider.get("type") == "lmstudio":
                    # Initialize LM Studio provider; do not load local model
                    try:
                        from .providers.lmstudio import LmStudioProvider

                        self._provider = LmStudioProvider(
                            host=str(provider.get("host", "127.0.0.1")),
                            port=provider.get("port", 1234),
                            model=provider.get("model"),
                            timeout=float(provider.get("timeout", 30.0)),
                        )
                        self._provider_type = "lmstudio"
                    except Exception as e:
                        # Defer failure: remember error and surface on use
                        self._provider = None
                        self._provider_type = "lmstudio"
                        self._provider_error = str(e)
                elif provider.get("type") == "ollama":
                    # Initialize Ollama provider; do not load local model
                    try:
                        from .providers.ollama import OllamaProvider

                        self._provider = OllamaProvider(
                            host=str(provider.get("host", "127.0.0.1")),
                            port=provider.get("port", 11434),
                            model=provider.get("model"),
                            timeout=float(provider.get("timeout", 30.0)),
                        )
                        self._provider_type = "ollama"
                    except Exception as e:
                        self._provider = None
                        self._provider_type = "ollama"
                        self._provider_error = str(e)
                elif provider.get("type") == "openai":
                    # Initialize OpenAI provider; defer failures
                    try:
                        from .providers.openai import OpenAIProvider

                        self._provider = OpenAIProvider(
                            api_key=str(provider.get("api_key", "")),
                            model=provider.get("model"),
                            base_url=str(provider.get("base_url"))
                            if provider.get("base_url")
                            else (
                                str(provider.get("host"))
                                if str(provider.get("host", "")).startswith("http")
                                else None
                            ),
                            host=str(provider.get("host"))
                            if not str(provider.get("host", "")).startswith("http")
                            else None,
                            port=provider.get("port"),
                            timeout=float(provider.get("timeout", 30.0)),
                        )
                        self._provider_type = "openai"
                    except Exception as e:
                        self._provider = None
                        self._provider_type = "openai"
                        self._provider_error = str(e)
                elif provider.get("type") == "claude-cli":
                    # Initialize Claude CLI provider
                    try:
                        from .providers.claude_cli import ClaudeCLIProvider

                        self._provider = ClaudeCLIProvider(
                            model=provider.get("model"),
                            binary=str(provider.get("binary", "claude")),
                            timeout=float(provider.get("timeout", 30.0)),
                            args=provider.get("args"),
                        )
                        self._provider_type = "claude-cli"
                    except Exception as e:
                        self._provider = None
                        self._provider_type = "claude-cli"
                        self._provider_error = str(e)
                elif provider.get("type") == "openai-cli":
                    # Initialize OpenAI CLI provider
                    try:
                        from .providers.openai_cli import OpenAICLIProvider

                        self._provider = OpenAICLIProvider(
                            model=provider.get("model"),
                            binary=str(provider.get("binary", "openai")),
                            timeout=float(provider.get("timeout", 30.0)),
                            args=provider.get("args"),
                        )
                        self._provider_type = "openai-cli"
                    except Exception as e:
                        self._provider = None
                        self._provider_type = "openai-cli"
                        self._provider_error = str(e)
        except Exception:
            # Fail closed: ignore provider config issues to preserve zero-config UX
            pass

        # Resolve model via ModelManager (respects env/local/project/global rules)
        if HAS_MODEL_MANAGER:
            try:
                from .models import ModelManager  # local import to avoid cycles

                manager = ModelManager()
                if provider_local_model_path:
                    # Use explicit file path; skip model id resolution
                    self.model_path = provider_local_model_path
                    # Adopt default output tokens if provided
                    try:
                        ot = (
                            provider.get("output_tokens")
                            if isinstance(provider, dict)
                            else None
                        )
                        if isinstance(ot, int) and ot > 0:
                            self.max_tokens = ot
                    except Exception:
                        pass
                elif self.model_id is None:
                    effective_id, decision = manager.resolve_effective_model(
                        provider_local_model=provider_local_model
                    )
                    # Only set model_id when decision is not legacy default;
                    # legacy default path uses MODEL_REPO/MODEL_FILE constants.
                    if decision != "legacy default":
                        self.model_id = effective_id
                # If we have a known model, pick its suggested output_tokens
                # when the user kept the default value
                if self.model_id and self.max_tokens == 4096:
                    try:
                        from .models import MODELS as _MODELS

                        if self.model_id in _MODELS:
                            maybe_ot = getattr(
                                _MODELS[self.model_id], "output_tokens", None
                            )
                            if isinstance(maybe_ot, int) and maybe_ot > 0:
                                self.max_tokens = maybe_ot
                    except Exception:
                        pass
            except Exception:
                # If anything goes wrong, proceed with legacy fallback
                pass

        # Load local model only when no external provider is configured
        if self._provider is None and self._router is None:
            self._ensure_model_loaded()

    def _ensure_model_loaded(self):
        """Load singleton llama.cpp model if not using provider/router."""
        global _model_instance, _model_lock

        if _model_instance is None:
            with _model_lock:
                if _model_instance is None:
                    model_path = self.model_path or self._download_model()
                    _model_instance = self._load_model(model_path)

        self.llm = _model_instance

    def _download_model(self) -> str:
        """Download model if not cached (first run)."""
        # Always prefer legacy cached model if present
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        legacy_model_path = MODEL_DIR / MODEL_FILE
        if legacy_model_path.exists():
            if self.verbose:
                print(f"✅ Using cached model from: {legacy_model_path}")
            return str(legacy_model_path)

        # Use ModelManager only when an explicit model_id is provided
        if HAS_MODEL_MANAGER and self.model_id:
            manager = ModelManager()

            if self.model_id not in MODELS:
                raise ValueError(
                    (
                        f"Unknown model: {self.model_id}. "
                        "Run 'chi-llm setup' to see available models."
                    )
                )
            model_info = MODELS[self.model_id]

            # Check if downloaded via manager
            model_path = manager.get_model_path(model_info.id)
            if model_path:
                if self.verbose:
                    print(f"✅ Using {model_info.name} from: {model_path}")
                return str(model_path)

            # Download selected model
            print(f"📥 Downloading {model_info.name} ({model_info.file_size_mb}MB)...")
            print(f"   Model will be cached in: {MODEL_DIR}")

            downloaded_path = hf_hub_download(
                repo_id=model_info.repo,
                filename=model_info.filename,
                local_dir=str(MODEL_DIR),
                resume_download=True,
            )

            manager.mark_downloaded(model_info.id)
            print(f"✅ {model_info.name} ready!\n")
            return downloaded_path

        # Fallback to legacy behavior (default Gemma model)
        print("📥 First-time setup: Downloading model (~200MB)...")
        print(f"   This only happens once. Model will be cached in: {MODEL_DIR}")

        downloaded_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILE,
            local_dir=str(MODEL_DIR),
            resume_download=True,
        )

        print("✅ Model ready! You won't see this message again.\n")
        return downloaded_path

    def _load_model(self, model_path: str) -> Llama:
        """Load llama.cpp model with sensible defaults."""
        try:
            if self.verbose:
                print("🤖 Loading model...")

            # Get context window and n_gpu_layers
            context_window = 32768  # Default
            n_gpu_layers = 0
            if HAS_MODEL_MANAGER and self.model_id:
                if self.model_id in MODELS:
                    context_window = MODELS[self.model_id].context_window
                    try:
                        n_gpu_layers = int(
                            getattr(MODELS[self.model_id], "n_gpu_layers", 0)
                        )
                    except Exception:
                        n_gpu_layers = 0
            # Allow provider.local to override for direct model_path usage
            if isinstance(self.provider_config, dict) and (
                self.provider_config.get("type") == "local"
            ):
                try:
                    pctx = self.provider_config.get("context_window")
                    if isinstance(pctx, int) and pctx > 0:
                        context_window = pctx
                except Exception:
                    pass
                try:
                    ngl = self.provider_config.get("n_gpu_layers")
                    if isinstance(ngl, int) and ngl >= 0:
                        n_gpu_layers = ngl
                except Exception:
                    pass

            model = Llama(
                model_path=model_path,
                n_ctx=context_window,
                n_threads=min(4, os.cpu_count() or 4),
                n_gpu_layers=n_gpu_layers,  # default 0 (CPU) unless overridden
                verbose=False,
            )

            if self.verbose:
                print("✅ Model loaded successfully!")

            return model
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text for a prompt (provider/router aware)."""
        # If an external provider is configured, route to it
        if self._router is not None:
            try:
                return self._router.generate(prompt, tags=self.tags, **kwargs)
            except Exception as e:
                raise RuntimeError(str(e))
        if self._provider is not None:
            try:
                return self._provider.generate(prompt, **kwargs)
            except Exception as e:
                raise RuntimeError(str(e))
        if self._provider_type is not None and self._provider is None:
            # External provider configured but unavailable
            hint = (
                f"Provider '{self._provider_type}' is configured but not available. "
                f"{self._provider_error or ''}"
            ).strip()
            raise RuntimeError(hint)

        # Check if we should use raw prompt (no formatting)
        use_raw = kwargs.pop("use_raw", False)

        params = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": 0.95,
            "top_k": 40,
            "min_p": 0.05,  # Add min_p parameter for better sampling
            "repeat_penalty": 1.1,
            "stop": [
                "<end_of_turn>",
                "<eos>",
                "</s>",
                "<start_of_turn>",
                "\n\n\n",
                "<|endoftext|>",
            ],
        }
        params.update(kwargs)

        # Use raw prompt or format for Gemma model
        if use_raw:
            # Use prompt as-is for simple completions
            formatted_prompt = prompt
        else:
            # Format for Gemma model (without BOS - llama.cpp adds it automatically)
            formatted_prompt = (
                f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
            )

        try:
            # Use lock to ensure thread-safe model access
            with _generation_lock:
                output = self.llm(formatted_prompt, echo=False, **params)
            return output["choices"][0]["text"].strip()
        except Exception as e:
            raise RuntimeError(f"Generation failed: {e}")

    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """Chat with optional history (provider/router aware)."""
        # Route to external provider if configured
        if self._router is not None:
            try:
                return self._router.chat(message, history=history, tags=self.tags)
            except Exception as e:
                raise RuntimeError(str(e))
        if self._provider is not None:
            try:
                return self._provider.chat(message, history=history)
            except Exception as e:
                raise RuntimeError(str(e))
        if self._provider_type is not None and self._provider is None:
            hint = (
                f"Provider '{self._provider_type}' is configured but not available. "
                f"{self._provider_error or ''}"
            ).strip()
            raise RuntimeError(hint)

        conversation = ""

        if history:
            for turn in history:
                if "user" in turn:
                    conversation += (
                        f"<start_of_turn>user\n{turn['user']}<end_of_turn>\n"
                    )
                if "assistant" in turn:
                    conversation += (
                        f"<start_of_turn>model\n{turn['assistant']}<end_of_turn>\n"
                    )

        conversation += (
            f"<start_of_turn>user\n{message}<end_of_turn>\n<start_of_turn>model\n"
        )

        try:
            # Use lock to ensure thread-safe model access
            with _generation_lock:
                output = self.llm(
                    conversation,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    echo=False,
                    stop=[
                        "<end_of_turn>",
                        "<eos>",
                        "</s>",
                        "<start_of_turn>",
                        "\n\n\n",
                        "<|endoftext|>",
                    ],
                )
            return output["choices"][0]["text"].strip()
        except Exception as e:
            raise RuntimeError(f"Chat failed: {e}")

    def complete(self, text: str, **kwargs) -> str:
        """Complete/continue text (provider/router aware)."""
        # Route to external provider if configured
        if self._router is not None:
            try:
                return self._router.complete(text, tags=self.tags, **kwargs)
            except Exception as e:
                raise RuntimeError(str(e))
        if self._provider is not None:
            try:
                return self._provider.complete(text, **kwargs)
            except Exception as e:
                raise RuntimeError(str(e))
        if self._provider_type is not None and self._provider is None:
            hint = (
                f"Provider '{self._provider_type}' is configured but not available. "
                f"{self._provider_error or ''}"
            ).strip()
            raise RuntimeError(hint)

        # For completion, we use a simpler format
        try:
            # Use lock to ensure thread-safe model access
            with _generation_lock:
                output = self.llm(
                    text,
                    max_tokens=kwargs.get("max_tokens", 100),
                    temperature=kwargs.get("temperature", 0.7),
                    echo=False,
                )
            return output["choices"][0]["text"].strip()
        except Exception as e:
            raise RuntimeError(f"Completion failed: {e}")

    def ask(self, question: str, context: Optional[str] = None, **kwargs) -> str:
        """Q&A helper; wraps generate with optional context."""
        if context:
            prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        else:
            prompt = f"Question: {question}\n\nAnswer:"

        return self.generate(prompt, **kwargs)

    def analyze(self, code: str, question: Optional[str] = None) -> str:
        """Quick code analysis helper (compat wrapper)."""
        if not question:
            question = "Analyze this code and explain what it does"

        return self.ask(question, context=code)

    def extract(
        self, text: str, format: str = "json", schema: Optional[Dict] = None
    ) -> str:
        """
        Extract structured data from text.

        Args:
            text: Input text
            format: Output format (json, list, etc.)
            schema: Optional schema description

        Returns:
            Extracted data in requested format

        Example:
            >>> llm.extract("John is 30 years old", format="json")
        """
        prompt = f"Extract information from this text and return as {format}"
        if schema:
            prompt += f" following this structure: {schema}"
        prompt += f":\n\n{text}\n\nExtracted {format}:"

        return self.generate(prompt, temperature=0.1)  # Low temperature for accuracy

    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """Summarize text to N sentences."""
        prompt = (
            f"Summarize this text in {max_sentences} sentences:\n\n{text}\n\nSummary:"
        )
        return self.generate(prompt, temperature=0.3)

    def translate(self, text: str, target_language: str = "English") -> str:
        """Translate text to the target language."""
        prompt = f"Translate this text to {target_language}:\n\n{text}\n\nTranslation:"
        return self.generate(prompt, temperature=0.1)

    def classify(self, text: str, categories: List[str]) -> str:
        """Classify text into one of the given categories."""
        categories_str = ", ".join(categories)
        prompt = (
            "Classify this text into one of these categories "
            f"[{categories_str}]:\n\n{text}\n\nCategory:"
        )
        return self.generate(prompt, temperature=0.1, max_tokens=50)

    def __call__(self, prompt: str, **kwargs) -> str:
        """Alias for generate()."""
        return self.generate(prompt, **kwargs)

    def __repr__(self) -> str:
        return f"MicroLLM(model='{MODEL_FILE}', temperature={self.temperature})"


# Convenience function for quick usage
def quick_llm(prompt: str, **kwargs) -> str:
    """
    Quick one-liner LLM usage without initialization.

    Example:
        >>> from chi_llm import quick_llm
        >>> print(quick_llm("Hello!"))
    """
    llm = MicroLLM()
    return llm.generate(prompt, **kwargs)
