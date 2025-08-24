"""
Model registry and management for chi_llm.

Changes:
- Curated models registry is now YAML-backed (package file: models.yaml).
- Falls back to a minimal built-in set if YAML not available.
- Zero-config default model can be controlled from YAML (key: zero_config_default).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import os
import logging
from importlib import resources

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
    # Optional tuning defaults
    n_gpu_layers: int = 0
    output_tokens: int = 4096


def _load_yaml_registry() -> Tuple[Dict[str, ModelInfo], Optional[str]]:
    """Load models registry from YAML if available.

    Order of attempts:
    1) CHI_LLM_MODELS_YAML env var path (if exists)
    2) Package resource chi_llm/models.yaml

    Returns:
        (models_dict, zero_config_default_id)
    """
    try:
        import yaml  # type: ignore
    except Exception:
        return {}, None

    def _parse(doc: dict) -> Tuple[Dict[str, ModelInfo], Optional[str]]:
        models: Dict[str, ModelInfo] = {}
        zero_default: Optional[str] = None
        if not isinstance(doc, dict):
            return models, None
        zero_default = doc.get("zero_config_default")
        for item in doc.get("models", []) or []:
            try:
                # Accept alias 'context_windows' if present
                ctx = item.get("context_window")
                if ctx is None:
                    ctx = item.get("context_windows")
                mi = ModelInfo(
                    id=str(item["id"]),
                    name=str(item.get("name", item["id"])),
                    size=str(item.get("size", "")),
                    file_size_mb=int(item.get("file_size_mb", 0)),
                    repo=str(item.get("repo", "")),
                    filename=str(item.get("filename", "")),
                    context_window=int(ctx if ctx is not None else 32768),
                    description=str(item.get("description", "")),
                    recommended_ram_gb=float(item.get("recommended_ram_gb", 2.0)),
                    tags=list(item.get("tags", []) or []),
                    n_gpu_layers=int(item.get("n_gpu_layers", 0) or 0),
                    output_tokens=int(item.get("output_tokens", 4096) or 4096),
                )
                models[mi.id] = mi
            except Exception:
                continue
        return models, zero_default

    # 1) Env path
    env_path = os.environ.get("CHI_LLM_MODELS_YAML")
    if env_path and Path(env_path).exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f) or {}
            return _parse(doc)
        except Exception:
            pass

    # 2) Package resource
    try:
        with resources.files(__package__).joinpath("models.yaml").open(
            "r", encoding="utf-8"
        ) as f:
            doc = yaml.safe_load(f) or {}
        return _parse(doc)
    except Exception:
        return {}, None


# Minimal built-in fallback when YAML not available (keep small)
MODELS: Dict[str, ModelInfo] = {
    "gemma-270m": ModelInfo(
        id="gemma-270m",
        name="Gemma 3 270M",
        size="270M",
        file_size_mb=385,
        repo="lmstudio-community/gemma-3-270m-it-GGUF",
        filename="gemma-3-270m-it-Q8_0.gguf",
        context_window=32768,
        description="Ultra-lightweight, fast inference, good for basic tasks",
        recommended_ram_gb=2.0,
        tags=["tiny", "fast", "cpu-friendly", "default"],
        n_gpu_layers=0,
        output_tokens=4096,
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
        n_gpu_layers=0,
        output_tokens=4096,
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
        n_gpu_layers=0,
        output_tokens=4096,
    ),
}

# Attempt to override from YAML registry
_YAML_MODELS, _YAML_ZERO_DEFAULT = _load_yaml_registry()
if _YAML_MODELS:
    MODELS = _YAML_MODELS


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
        """Get possible config paths."""
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
        """Load config with precedence and flags."""
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

        # Fill built-in/YAML default if still unset
        if not self.config.get("default_model"):
            self.config["default_model"] = _YAML_ZERO_DEFAULT or "gemma-270m"
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
        # Best-effort source label and paths
        config_source = "default"
        env_cfg = os.environ.get("CHI_LLM_CONFIG")
        local_path = (
            (Path.cwd() / ".chi_llm.json")
            if (Path.cwd() / ".chi_llm.json").exists()
            else None
        )
        # Walk up for project path (excluding CWD already checked)
        project_path = None
        current = Path.cwd().parent
        while current != current.parent:
            candidate = current / ".chi_llm.json"
            if candidate.exists():
                project_path = candidate
                break
            current = current.parent
        global_path = self.config_paths.get("global") if self.allow_global else None
        if env_cfg:
            config_source = "env"
        elif local_path is not None:
            config_source = "local"
        elif project_path is not None:
            config_source = "project"
        elif global_path is not None and global_path.exists():
            config_source = "global"

        return {
            "total_models": len(MODELS),
            "downloaded": len([m for m in MODELS if self.is_downloaded(m)]),
            "current_model": self.config["default_model"],
            "available_ram_gb": self._get_available_ram(),
            "recommended_model": self.recommend_model().id,
            "config_source": config_source,
            "config_path": str(self.config_paths.get(config_source, "built-in")),
            "resolution_mode": self.resolution_mode,
            "allow_global": self.allow_global,
            "explicit_default": self.has_explicit_default(),
            "sources": {
                "env_cfg": bool(env_cfg),
                "env_model": bool(os.environ.get("CHI_LLM_MODEL")),
                "local": str(local_path) if local_path else None,
                "project": str(project_path) if project_path else None,
                "global": str(global_path)
                if (global_path and global_path.exists())
                else None,
            },
        }

    def resolve_effective_model(
        self, provider_local_model: Optional[str] = None
    ) -> Tuple[str, str]:
        """Decide which model would be effectively used and why.

        Returns a tuple of (model_id, decision_note):
        - explicit default: default_model from env/project/local/global
        - provider local fallback: no explicit default; provider.type=local
          provides model
        - legacy default: built-in default when nothing else provided
        """
        # Explicit default wins
        if self.has_explicit_default():
            return self.config.get("default_model", "gemma-270m"), "explicit default"
        # Provider local fallback (if declared)
        if isinstance(provider_local_model, str) and provider_local_model:
            return provider_local_model, "provider local fallback"
        # Legacy built-in default
        return self.config.get("default_model", "gemma-270m"), "legacy default"
