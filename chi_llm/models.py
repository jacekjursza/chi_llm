"""
Model registry and management for chi_llm.
Provides multiple model options with different sizes and capabilities.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import os
import logging

logger = logging.getLogger(__name__)

# Model directory
MODEL_DIR = Path.home() / ".cache" / "chi_llm"


@dataclass
class ModelInfo:
    """Information about an available model."""

    id: str
    name: str
    size: str  # Human-readable size (e.g., "1.3B")
    file_size_mb: int  # Actual file size in MB
    repo: str  # HuggingFace repo
    filename: str  # GGUF filename
    context_window: int
    description: str
    recommended_ram_gb: float
    tags: List[str]


# Model Registry - curated list of best small models
MODELS = {
    # Tiny models (~270M)
    "gemma-270m": ModelInfo(
        id="gemma-270m",
        name="Gemma 3 270M",
        size="270M",
        file_size_mb=385,  # Q8_0 is bigger than Q4_K_M
        repo="lmstudio-community/gemma-3-270m-it-GGUF",
        filename="gemma-3-270m-it-Q8_0.gguf",  # Use Q8_0 for better quality
        context_window=32768,
        description="Ultra-lightweight, fast inference, good for basic tasks",
        recommended_ram_gb=2.0,
        tags=["tiny", "fast", "cpu-friendly", "default"],
    ),
    # Small Qwen3 models
    "qwen3-0.6b": ModelInfo(
        id="qwen3-0.6b",
        name="Qwen3 0.6B",
        size="0.6B",
        file_size_mb=500,
        repo="Qwen/Qwen3-0.6B-GGUF",
        filename="qwen3-0.6b-instruct-q5_k_m.gguf",
        context_window=32768,
        description="Tiny but capable, supports thinking/non-thinking modes",
        recommended_ram_gb=1.5,
        tags=["tiny", "versatile", "thinking-mode"],
    ),
    "qwen3-1.7b": ModelInfo(
        id="qwen3-1.7b",
        name="Qwen3 1.7B",
        size="1.7B",
        file_size_mb=1100,
        repo="Qwen/Qwen3-1.7B-GGUF",
        filename="qwen3-1.7b-instruct-q5_k_m.gguf",
        context_window=32768,
        description="Best performing model under 2B, thinking mode support",
        recommended_ram_gb=3.0,
        tags=["small", "balanced", "recommended", "thinking-mode"],
    ),
    "stablelm-2-1.6b": ModelInfo(
        id="stablelm-2-1.6b",
        name="StableLM 2 1.6B",
        size="1.6B",
        file_size_mb=1100,
        repo="lmstudio-community/stablelm-2-1_6b-GGUF",
        filename="stablelm-2-1_6b-Q4_K_M.gguf",
        context_window=4096,
        description="Stable Diffusion's language model, good general performance",
        recommended_ram_gb=3.0,
        tags=["small", "stable"],
    ),
    # 2B+ models
    "gemma2-2b": ModelInfo(
        id="gemma2-2b",
        name="Gemma 2 2B",
        size="2B",
        file_size_mb=1420,
        repo="bartowski/gemma-2-2b-it-GGUF",
        filename="gemma-2-2b-it-Q4_K_M.gguf",
        context_window=8192,
        description="Google's efficient 2B model, great quality/size ratio",
        recommended_ram_gb=4.0,
        tags=["medium", "google", "efficient"],
    ),
    "phi2-2.7b": ModelInfo(
        id="phi2-2.7b",
        name="Phi-2",
        size="2.7B",
        file_size_mb=1680,
        repo="lmstudio-community/Phi-2-GGUF",
        filename="Phi-2-Q4_K_M.gguf",
        context_window=2048,
        description="Microsoft's small model, strong reasoning capabilities",
        recommended_ram_gb=4.0,
        tags=["medium", "microsoft", "reasoning"],
    ),
    # 3B+ models
    "stablelm-3b": ModelInfo(
        id="stablelm-3b",
        name="StableLM 3B",
        size="2.8B",
        file_size_mb=1800,
        repo="lmstudio-community/stablelm-3b-4e1t-GGUF",
        filename="stablelm-3b-4e1t-Q4_K_M.gguf",
        context_window=4096,
        description="Best performing 3B model, trained on 4 trillion tokens",
        recommended_ram_gb=4.0,
        tags=["medium", "high-quality"],
    ),
    "phi3-mini": ModelInfo(
        id="phi3-mini",
        name="Phi-3 Mini",
        size="3.8B",
        file_size_mb=2400,
        repo="microsoft/Phi-3-mini-4k-instruct-gguf",
        filename="Phi-3-mini-4k-instruct-q4.gguf",
        context_window=4096,
        description="Microsoft's champion model, performs like 7B but runs like 3B",
        recommended_ram_gb=5.0,
        tags=["large", "best-quality", "microsoft", "recommended"],
    ),
    # 4B models
    "qwen3-8b": ModelInfo(
        id="qwen3-8b",
        name="Qwen3 8B",
        size="8B",
        file_size_mb=5500,
        repo="Qwen/Qwen3-8B-GGUF",
        filename="qwen3-8b-instruct-q5_k_m.gguf",
        context_window=32768,
        description="Latest Qwen3, excellent reasoning and multilingual support",
        recommended_ram_gb=9.0,
        tags=["large", "multilingual", "latest", "thinking-mode"],
    ),
    "gemma2-9b": ModelInfo(
        id="gemma2-9b",
        name="Gemma 2 9B (Q2_K)",
        size="9B",
        file_size_mb=3900,
        repo="bartowski/gemma-2-9b-it-GGUF",
        filename="gemma-2-9b-it-Q2_K.gguf",
        context_window=8192,
        description="Heavily quantized 9B model that runs like 4B",
        recommended_ram_gb=6.0,
        tags=["large", "compressed", "powerful"],
    ),
    # New blazingly fast models
    "liquid-lfm2-1.2b": ModelInfo(
        id="liquid-lfm2-1.2b",
        name="Liquid LFM2 1.2B",
        size="1.2B",
        file_size_mb=1250,
        repo="LiquidAI/LFM2-1.2B-GGUF",
        filename="LFM2-1.2B-Q8_0.gguf",
        context_window=32768,
        description="Blazingly fast hybrid architecture, excels at math & multilingual",
        recommended_ram_gb=2.5,
        tags=["small", "fast", "multilingual", "math", "hybrid"],
    ),
    "deepseek-r1-qwen-1.5b": ModelInfo(
        id="deepseek-r1-qwen-1.5b",
        name="DeepSeek R1 Distill Qwen 1.5B",
        size="1.5B",
        file_size_mb=1600,
        repo="bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF",
        filename="DeepSeek-R1-Distill-Qwen-1.5B-Q5_K_M.gguf",
        context_window=32768,
        description="Distilled from DeepSeek R1, strong reasoning capabilities",
        recommended_ram_gb=3.0,
        tags=["small", "reasoning", "distilled"],
    ),
    # Qwen3 thinking models
    "qwen3-4b-thinking": ModelInfo(
        id="qwen3-4b-thinking",
        name="Qwen3 4B Thinking 2507",
        size="4B",
        file_size_mb=2800,
        repo="qwen/qwen3-4b-thinking-2507-gguf",
        filename="qwen3-4b-thinking-2507-Q5_K_M.gguf",
        context_window=262144,  # 256K context!
        description="Advanced reasoning with thinking capability, 256K context",
        recommended_ram_gb=5.0,
        tags=["medium", "reasoning", "thinking", "long-context", "256k"],
    ),
    "qwen3-4b": ModelInfo(
        id="qwen3-4b",
        name="Qwen3 4B Instruct 2507",
        size="4B",
        file_size_mb=2800,
        repo="qwen/qwen3-4b-2507-gguf",
        filename="qwen3-4b-2507-Q5_K_M.gguf",
        context_window=262144,  # 256K context!
        description="Enhanced general capabilities, 256K context",
        recommended_ram_gb=5.0,
        tags=["medium", "general", "long-context", "256k"],
    ),
    # Qwen2.5-coder series
    "qwen2.5-coder-0.5b": ModelInfo(
        id="qwen2.5-coder-0.5b",
        name="Qwen2.5 Coder 0.5B",
        size="0.5B",
        file_size_mb=500,
        repo="Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF",
        filename="qwen2.5-coder-0.5b-instruct-q5_k_m.gguf",
        context_window=32768,
        description="Tiny coding assistant, perfect for IDE integration",
        recommended_ram_gb=1.5,
        tags=["tiny", "coding", "fast", "ide"],
    ),
    "qwen2.5-coder-1.5b": ModelInfo(
        id="qwen2.5-coder-1.5b",
        name="Qwen2.5 Coder 1.5B",
        size="1.5B",
        file_size_mb=1100,
        repo="Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF",
        filename="qwen2.5-coder-1.5b-instruct-q5_k_m.gguf",
        context_window=32768,
        description="Small but capable coding model",
        recommended_ram_gb=2.5,
        tags=["small", "coding", "balanced"],
    ),
    "qwen2.5-coder-3b": ModelInfo(
        id="qwen2.5-coder-3b",
        name="Qwen2.5 Coder 3B",
        size="3B",
        file_size_mb=2100,
        repo="Qwen/Qwen2.5-Coder-3B-Instruct-GGUF",
        filename="qwen2.5-coder-3b-instruct-q5_k_m.gguf",
        context_window=32768,
        description="Powerful coding model with good performance",
        recommended_ram_gb=4.0,
        tags=["medium", "coding", "powerful"],
    ),
    "qwen2.5-coder-7b": ModelInfo(
        id="qwen2.5-coder-7b",
        name="Qwen2.5 Coder 7B",
        size="7B",
        file_size_mb=4900,
        repo="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
        filename="qwen2.5-coder-7b-instruct-q5_k_m.gguf",
        context_window=32768,
        description="Professional-grade coding model, excellent for complex tasks",
        recommended_ram_gb=8.0,
        tags=["large", "coding", "professional", "complex"],
    ),
}


class ModelManager:
    """Manages model downloads and switching.

    Configuration priority (highest to lowest):
    1. Environment variables (CHI_LLM_MODEL, CHI_LLM_CONFIG)
    2. Local project config (.chi_llm.json in current directory)
    3. User project config (traverse up to find .chi_llm.json)
    4. Global user config (~/.cache/chi_llm/model_config.json)
    5. Default configuration
    """

    def __init__(self, config_path: Optional[str] = None):
        # Resolution controls
        self.resolution_mode = os.environ.get(
            "CHI_LLM_RESOLUTION_MODE", "project-first"
        ).strip()
        self.allow_global = os.environ.get("CHI_LLM_ALLOW_GLOBAL", "0").strip() in {
            "1",
            "true",
            "True",
        }

        self.config_paths = self._get_config_paths(config_path)
        # For saving (global user config)
        self.config_file = self.config_paths["global"]
        # Tracks whether default_model came from an explicit source (not built-in)
        self._explicit_default: bool = False
        self.load_config()

    def _get_config_paths(self, custom_path: Optional[str] = None) -> Dict[str, Path]:
        """Get all possible config paths in priority order."""
        paths = {}

        # 1. Custom path if provided
        if custom_path:
            paths["custom"] = Path(custom_path)

        # 2. Environment variable
        if "CHI_LLM_CONFIG" in os.environ:
            paths["env"] = Path(os.environ["CHI_LLM_CONFIG"])

        # 3. Local project config (current directory)
        local_config = Path.cwd() / ".chi_llm.json"
        if local_config.exists():
            paths["local"] = local_config

        # 4. Project config (traverse up to find)
        current = Path.cwd()
        while current != current.parent:
            project_config = current / ".chi_llm.json"
            if project_config.exists():
                paths["project"] = project_config
                break
            current = current.parent

        # 5. Global user config
        paths["global"] = MODEL_DIR / "model_config.json"

        return paths

    def load_config(self):
        """Load config with precedence and flags.

        Default (project-first): local -> project -> env-file -> custom -> [global*]
        Env-first: env-file -> local -> project -> custom -> [global*]
        * Global applies only when CHI_LLM_ALLOW_GLOBAL is set truthy or enabled
          in project config. CHI_LLM_MODEL always overrides explicitly.
        """
        # Base defaults
        self.config = {
            # default_model intentionally assigned later; track explicitness
            "downloaded_models": [],
            "preferred_context": 8192,
            "preferred_max_tokens": 4096,
        }

        # Peek flags from project files if not set in env
        self._apply_peek_flags()

        # Determine ordered sources
        sources: List[str]
        if self.resolution_mode == "env-first":
            sources = ["env", "local", "project", "custom"]
        else:  # project-first (default)
            sources = ["local", "project", "env", "custom"]
        if self.allow_global:
            sources.append("global")

        # Apply file-based sources
        for source in sources:
            if source not in self.config_paths:
                continue
            path = self.config_paths[source]
            if not path:
                continue
            try:
                if path.exists():
                    with open(path, "r") as f:
                        loaded = json.load(f)
                    self._merge_loaded_config(loaded)
                    logger.debug(f"Loaded config from {source}: {path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {path}: {e}")

        # Environment variable overrides (highest)
        model_id = os.environ.get("CHI_LLM_MODEL")
        if model_id and model_id in MODELS:
            self.config["default_model"] = model_id
            self._explicit_default = True
            logger.debug(f"Using model from env: {model_id}")

        if "CHI_LLM_CONTEXT" in os.environ:
            try:
                self.config["preferred_context"] = int(os.environ["CHI_LLM_CONTEXT"])
            except ValueError:
                pass

        if "CHI_LLM_MAX_TOKENS" in os.environ:
            try:
                self.config["preferred_max_tokens"] = int(
                    os.environ["CHI_LLM_MAX_TOKENS"]
                )
            except ValueError:
                pass

        # Fill built-in default if still unset
        if not self.config.get("default_model"):
            self.config["default_model"] = "gemma-270m"
            # Only built-in, keep _explicit_default as-is (likely False)

    def _apply_peek_flags(self) -> None:
        """Peek allow_global/resolution_mode from project files (env wins)."""
        # If env provided, keep as-is; otherwise peek files
        if os.environ.get("CHI_LLM_RESOLUTION_MODE") is None:
            # Try local first
            local = self.config_paths.get("local")
            project = self.config_paths.get("project")
            for p in [local, project]:
                try:
                    if p and p.exists():
                        data = json.loads(p.read_text(encoding="utf-8"))
                        mode = str(data.get("resolution_mode", "")).strip()
                        if mode in {"project-first", "env-first"}:
                            self.resolution_mode = mode
                            break
                except Exception:
                    pass
        if os.environ.get("CHI_LLM_ALLOW_GLOBAL") is None and not self.allow_global:
            local = self.config_paths.get("local")
            project = self.config_paths.get("project")
            for p in [local, project]:
                try:
                    if p and p.exists():
                        data = json.loads(p.read_text(encoding="utf-8"))
                        ag = data.get("allow_global")
                        if isinstance(ag, bool):
                            self.allow_global = ag
                            break
                except Exception:
                    pass

    def _merge_loaded_config(self, loaded: Dict) -> None:
        # Recognize default_model as explicit when provided
        if isinstance(loaded, dict) and loaded.get("default_model"):
            self._explicit_default = True
        self.config.update(loaded or {})

    def has_explicit_default(self) -> bool:
        return self._explicit_default

    def save_config(self, target: str = "global"):
        """Save model configuration.

        Args:
            target: Where to save - 'global', 'local', or specific path
        """
        if target == "local":
            save_path = Path.cwd() / ".chi_llm.json"
        elif target == "global":
            save_path = self.config_file
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
        else:
            save_path = Path(target)

        with open(save_path, "w") as f:
            json.dump(self.config, f, indent=2)
        logger.info(f"Saved config to {save_path}")

    def get_current_model(self) -> ModelInfo:
        """Get currently selected model."""
        model_id = self.config.get("default_model", "gemma-270m")
        return MODELS[model_id]

    def list_models(self, show_all: bool = False) -> List[ModelInfo]:
        """List available models."""
        if show_all:
            return list(MODELS.values())

        # Filter by system capabilities
        available_ram = self._get_available_ram()
        suitable_models = []

        for model in MODELS.values():
            if model.recommended_ram_gb <= available_ram:
                suitable_models.append(model)

        return suitable_models

    def is_downloaded(self, model_id: str) -> bool:
        """Check if model is downloaded."""
        if model_id not in MODELS:
            return False

        model = MODELS[model_id]
        model_path = MODEL_DIR / model.filename
        return model_path.exists()

    def get_model_path(self, model_id: str) -> Optional[Path]:
        """Get path to downloaded model."""
        if not self.is_downloaded(model_id):
            return None

        model = MODELS[model_id]
        return MODEL_DIR / model.filename

    def set_default_model(self, model_id: str, save_target: str = "global"):
        """Set default model.

        Args:
            model_id: Model ID to set as default
            save_target: Where to save - 'global', 'local', or path
        """
        if model_id not in MODELS:
            raise ValueError(f"Unknown model: {model_id}")

        self.config["default_model"] = model_id
        self.save_config(save_target)

    def mark_downloaded(self, model_id: str):
        """Mark model as downloaded."""
        if model_id not in self.config["downloaded_models"]:
            self.config["downloaded_models"].append(model_id)
            self.save_config()

    def _get_available_ram(self) -> float:
        """Get available RAM in GB."""
        try:
            import psutil

            return psutil.virtual_memory().total / (1024**3)
        except ImportError:
            # Assume 8GB if psutil not available
            return 8.0

    def get_download_info(self, model_id: str) -> Tuple[str, str]:
        """Get download info for a model (repo, filename)."""
        if model_id not in MODELS:
            raise ValueError(f"Unknown model: {model_id}")

        model = MODELS[model_id]
        return model.repo, model.filename

    def recommend_model(self) -> ModelInfo:
        """Recommend best model for system."""
        available_ram = self._get_available_ram()

        # Find best model that fits in RAM
        best_model = MODELS["gemma-270m"]  # Default fallback

        for model in MODELS.values():
            if (
                "recommended" in model.tags
                and model.recommended_ram_gb <= available_ram * 0.7
            ):
                best_model = model
                break

        return best_model

    def get_model_stats(self) -> Dict:
        """Get statistics about models."""
        # Best-effort source label (indicative only)
        config_source = "default"
        env_cfg = os.environ.get("CHI_LLM_CONFIG")
        if env_cfg:
            config_source = "env"
        elif (Path.cwd() / ".chi_llm.json").exists():
            config_source = "local"
        else:
            # Walk up for project
            current = Path.cwd()
            while current != current.parent:
                if (current / ".chi_llm.json").exists():
                    config_source = "project"
                    break
                current = current.parent
        if (
            self.allow_global
            and self.config_paths.get("global", Path("/dev/null")).exists()
        ):
            # If no other source found, label as global
            if config_source == "default":
                config_source = "global"

        return {
            "total_models": len(MODELS),
            "downloaded": len([m for m in MODELS if self.is_downloaded(m)]),
            "current_model": self.config["default_model"],
            "available_ram_gb": self._get_available_ram(),
            "recommended_model": self.recommend_model().id,
            "config_source": config_source,
            "config_path": str(self.config_paths.get(config_source, "built-in")),
        }


def format_model_info(
    model: ModelInfo, is_downloaded: bool = False, is_current: bool = False
) -> str:
    """Format model information for display."""
    status = ""
    if is_current:
        status = " [CURRENT]"
    elif is_downloaded:
        status = " [Downloaded]"

    return f"""
{model.name} ({model.size}){status}
  ID: {model.id}
  Size: {model.file_size_mb}MB | RAM: {model.recommended_ram_gb}GB
  Context: {model.context_window:,} tokens
  Description: {model.description}
  Tags: {', '.join(model.tags)}
"""


## Deprecated: get_model_by_size moved out in future versions
