"""
Model registry and management for chi_llm.
Provides multiple model options with different sizes and capabilities.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import os

# Model directory
MODEL_DIR = Path.home() / '.cache' / 'chi_llm'


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
        file_size_mb=200,
        repo="lmstudio-community/gemma-3-270m-it-GGUF",
        filename="gemma-3-270m-it-Q4_K_M.gguf",
        context_window=32768,
        description="Ultra-lightweight, fast inference, good for basic tasks",
        recommended_ram_gb=2.0,
        tags=["tiny", "fast", "cpu-friendly", "default"]
    ),
    
    # 1B+ models
    "qwen2-1.5b": ModelInfo(
        id="qwen2-1.5b",
        name="Qwen2 1.5B",
        size="1.5B",
        file_size_mb=980,
        repo="Qwen/Qwen2.5-1.5B-Instruct-GGUF",
        filename="qwen2.5-1.5b-instruct-q4_k_m.gguf",
        context_window=32768,
        description="Best performing model under 2B, excellent for edge devices",
        recommended_ram_gb=3.0,
        tags=["small", "balanced", "recommended"]
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
        tags=["small", "stable"]
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
        tags=["medium", "google", "efficient"]
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
        tags=["medium", "microsoft", "reasoning"]
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
        tags=["medium", "high-quality"]
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
        tags=["large", "best-quality", "microsoft", "recommended"]
    ),
    
    # 4B models
    "qwen2.5-3b": ModelInfo(
        id="qwen2.5-3b",
        name="Qwen2.5 3B",
        size="3B",
        file_size_mb=2100,
        repo="Qwen/Qwen2.5-3B-Instruct-GGUF",
        filename="qwen2.5-3b-instruct-q4_k_m.gguf",
        context_window=32768,
        description="Latest Qwen model, excellent multilingual support",
        recommended_ram_gb=5.0,
        tags=["large", "multilingual", "latest"]
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
        tags=["large", "compressed", "powerful"]
    )
}


class ModelManager:
    """Manages model downloads and switching."""
    
    def __init__(self):
        self.config_file = MODEL_DIR / "model_config.json"
        self.load_config()
    
    def load_config(self):
        """Load model configuration."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "default_model": "gemma-270m",
                "downloaded_models": [],
                "preferred_context": 8192,
                "preferred_max_tokens": 4096
            }
    
    def save_config(self):
        """Save model configuration."""
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
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
    
    def set_default_model(self, model_id: str):
        """Set default model."""
        if model_id not in MODELS:
            raise ValueError(f"Unknown model: {model_id}")
        
        self.config["default_model"] = model_id
        self.save_config()
    
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
            if "recommended" in model.tags and model.recommended_ram_gb <= available_ram * 0.7:
                best_model = model
                break
        
        return best_model
    
    def get_model_stats(self) -> Dict:
        """Get statistics about models."""
        return {
            "total_models": len(MODELS),
            "downloaded": len([m for m in MODELS if self.is_downloaded(m)]),
            "current_model": self.config["default_model"],
            "available_ram_gb": self._get_available_ram(),
            "recommended_model": self.recommend_model().id
        }


def format_model_info(model: ModelInfo, is_downloaded: bool = False, is_current: bool = False) -> str:
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


def get_model_by_size(size_category: str) -> Optional[ModelInfo]:
    """Get recommended model by size category."""
    size_map = {
        "tiny": "gemma-270m",
        "small": "qwen2-1.5b",
        "medium": "gemma2-2b",
        "large": "phi3-mini"
    }
    
    model_id = size_map.get(size_category.lower())
    return MODELS.get(model_id) if model_id else None