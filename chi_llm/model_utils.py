from typing import Optional

from .models import ModelInfo, MODELS


def format_model_info(
    model: ModelInfo, is_downloaded: bool = False, is_current: bool = False
) -> str:
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
    size_map = {
        "tiny": "gemma-270m",
        "small": "qwen3-1.7b",
        "medium": "gemma2-2b",
        "large": "phi3-mini",
    }
    model_id = size_map.get(size_category.lower())
    return MODELS.get(model_id) if model_id else None
