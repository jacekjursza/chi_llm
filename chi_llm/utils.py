"""
Utility functions for chi_llm.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dicts, with overrides taking precedence."""
    for key, value in (overrides or {}).items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration with sensible precedence and deep-merge.

    Merge order (later overrides earlier):
    1. Defaults
    2. Project files in CWD: .chi_llm.yaml/.yml/.json (first found)
    3. Provided config_path (if any) — explicit path should override project
    4. CHI_LLM_CONFIG (file path or inline JSON) — always overrides

    Returns:
        Configuration dictionary
    """
    # 1) Defaults
    config: Dict[str, Any] = {
        "model": {"temperature": 0.7, "max_tokens": 4096, "top_p": 0.95, "top_k": 40},
        "cache_dir": str(Path.home() / ".cache" / "chi_llm"),
        "verbose": False,
        "provider": {},  # optional provider configuration
        # List of directories to recursively search for local GGUF models
        # when discovering models for the 'local' provider.
        "auto_discovery_gguf_paths": [],
    }

    # 2) Project file in CWD
    for filename in [".chi_llm.yaml", ".chi_llm.yml", ".chi_llm.json"]:
        if Path(filename).exists():
            cfg = _load_file_config(filename, {})
            config = _deep_merge(config, cfg)
            break

    # 3) Explicit path (should override project)
    if config_path and Path(config_path).exists():
        cfg = _load_file_config(config_path, {})
        config = _deep_merge(config, cfg)

    # 4) Environment override
    env_cfg = os.environ.get("CHI_LLM_CONFIG")
    if env_cfg:
        if Path(env_cfg).exists():
            cfg = _load_file_config(env_cfg, {})
            config = _deep_merge(config, cfg)
        else:
            try:
                cfg = json.loads(env_cfg)
                if isinstance(cfg, dict):
                    config = _deep_merge(config, cfg)
            except json.JSONDecodeError:
                # Ignore invalid JSON in env var
                pass

    # Provider-specific environment overrides (always highest priority)
    provider_type = os.environ.get("CHI_LLM_PROVIDER_TYPE")
    if provider_type:
        config.setdefault("provider", {})
        config["provider"]["type"] = provider_type

    provider_host = os.environ.get("CHI_LLM_PROVIDER_HOST")
    if provider_host:
        config.setdefault("provider", {})
        config["provider"]["host"] = provider_host

    provider_port = os.environ.get("CHI_LLM_PROVIDER_PORT")
    if provider_port:
        # store as int when possible
        try:
            port_int = int(provider_port)
        except ValueError:
            port_int = provider_port  # keep raw
        config.setdefault("provider", {})
        config["provider"]["port"] = port_int

    provider_key = os.environ.get("CHI_LLM_PROVIDER_API_KEY")
    if provider_key:
        config.setdefault("provider", {})
        config["provider"]["api_key"] = provider_key

    provider_model = os.environ.get("CHI_LLM_PROVIDER_MODEL")
    if provider_model:
        config.setdefault("provider", {})
        config["provider"]["model"] = provider_model

    provider_model_path = os.environ.get("CHI_LLM_PROVIDER_MODEL_PATH")
    if provider_model_path:
        config.setdefault("provider", {})
        config["provider"]["model_path"] = provider_model_path

    # Optional: define GGUF search roots via env (pathsep-separated)
    gguf_paths_env = os.environ.get("CHI_LLM_GGUF_PATHS")
    if gguf_paths_env:
        paths = [p.strip() for p in gguf_paths_env.split(os.pathsep) if p.strip()]
        if paths:
            config["auto_discovery_gguf_paths"] = paths

    # Optional local-tuning overrides for the 'local' provider
    provider_ctx = os.environ.get("CHI_LLM_PROVIDER_CONTEXT_WINDOW") or os.environ.get(
        "CHI_LLM_PROVIDER_CONTEXT"
    )
    if provider_ctx:
        try:
            config.setdefault("provider", {})
            config["provider"]["context_window"] = int(provider_ctx)
        except Exception:
            pass

    provider_ngl = os.environ.get("CHI_LLM_PROVIDER_N_GPU_LAYERS")
    if provider_ngl:
        try:
            config.setdefault("provider", {})
            config["provider"]["n_gpu_layers"] = int(provider_ngl)
        except Exception:
            pass

    provider_ot = os.environ.get("CHI_LLM_PROVIDER_OUTPUT_TOKENS")
    if provider_ot:
        try:
            config.setdefault("provider", {})
            config["provider"]["output_tokens"] = int(provider_ot)
        except Exception:
            pass

    return config


def _load_file_config(filepath: str, defaults: Dict) -> Dict[str, Any]:
    """Load configuration from file."""
    path = Path(filepath)

    try:
        if path.suffix in [".yaml", ".yml"]:
            with open(path, "r") as f:
                config = yaml.safe_load(f) or {}
        elif path.suffix == ".json":
            with open(path, "r") as f:
                config = json.load(f)
        else:
            # Try to detect format
            with open(path, "r") as f:
                content = f.read()
                try:
                    config = json.loads(content)
                except json.JSONDecodeError:
                    config = yaml.safe_load(content) or {}

        # Merge with defaults
        return {**defaults, **config}
    except Exception as e:
        print(f"Warning: Could not load config from {filepath}: {e}")
        return defaults


def truncate_text(
    text: str, max_length: int = 20000, suffix: str = "\n... (truncated)"
) -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum character length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_chat_history(history: List[Dict[str, str]]) -> str:
    """
    Format chat history for model input.

    Args:
        history: List of chat messages

    Returns:
        Formatted chat string
    """
    formatted = []

    for message in history:
        if "user" in message:
            formatted.append(f"<start_of_turn>user\n{message['user']}<end_of_turn>")
        if "assistant" in message:
            formatted.append(
                f"<start_of_turn>model\n{message['assistant']}<end_of_turn>"
            )
        if "system" in message:
            formatted.append(f"System: {message['system']}")

    return "\n".join(formatted)


def count_tokens_approx(text: str) -> int:
    """
    Approximate token count (rough estimate).

    Args:
        text: Text to count tokens for

    Returns:
        Approximate token count
    """
    # Rough approximation: ~4 characters per token
    return len(text) // 4


def validate_response(response: str, min_length: int = 1) -> bool:
    """
    Validate model response.

    Args:
        response: Model response
        min_length: Minimum valid length

    Returns:
        True if valid response
    """
    if not response or len(response.strip()) < min_length:
        return False

    # Check for common error patterns
    error_patterns = ["error:", "failed to", "could not", "unable to"]

    lower_response = response.lower()
    for pattern in error_patterns:
        if lower_response.startswith(pattern):
            return False

    return True


def clean_response(response: str) -> str:
    """
    Clean up model response.

    Args:
        response: Raw model response

    Returns:
        Cleaned response
    """
    # Remove extra whitespace
    response = response.strip()

    # Remove multiple newlines
    while "\n\n\n" in response:
        response = response.replace("\n\n\n", "\n\n")

    # Remove common artifacts
    artifacts = [
        "<end_of_turn>",
        "<eos>",
        "</s>",
        "<start_of_turn>",
        "<|endoftext|>",
        "[END]",
        "[DONE]",
        "<|im_end|>",
        "<|im_start|>",
    ]

    for artifact in artifacts:
        response = response.replace(artifact, "")

    return response.strip()


def split_into_chunks(
    text: str, chunk_size: int = 15000, overlap: int = 500
) -> List[str]:
    """
    Split text into overlapping chunks for processing.

    Args:
        text: Text to split
        chunk_size: Size of each chunk
        overlap: Overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence end
            for sep in [". ", ".\n", "! ", "!\n", "? ", "?\n"]:
                last_sep = text.rfind(sep, start, end)
                if last_sep != -1:
                    end = last_sep + len(sep)
                    break

        chunks.append(text[start:end])
        start = end - overlap if end < len(text) else end

    return chunks


def merge_responses(responses: List[str], task: str = "default") -> str:
    """
    Merge multiple model responses intelligently.

    Args:
        responses: List of responses to merge
        task: Type of task (affects merging strategy)

    Returns:
        Merged response
    """
    if not responses:
        return ""

    if len(responses) == 1:
        return responses[0]

    if task == "summarize":
        # For summaries, combine key points
        return "\n\n".join(responses)
    elif task == "extract":
        # For extraction, merge data
        return "\n".join(responses)
    else:
        # Default: concatenate with separator
        return "\n\n---\n\n".join(responses)


def get_model_info() -> Dict[str, Any]:
    """
    Get information about the current model.

    Returns:
        Dictionary with model information
    """
    from . import MODEL_FILE, MODEL_REPO

    return {
        "name": "Gemma 3 270M",
        "file": MODEL_FILE,
        "repo": MODEL_REPO,
        "parameters": "270M",
        "context_window": 8192,
        "quantization": "Q4_K_M",
        "size_mb": 200,
    }


def estimate_processing_time(text_length: int) -> float:
    """
    Estimate processing time in seconds.

    Args:
        text_length: Length of text to process

    Returns:
        Estimated time in seconds
    """
    # Rough estimate based on CPU processing
    # ~500 characters per second on average hardware
    return max(1.0, text_length / 500)


def is_code(text: str) -> bool:
    """
    Simple heuristic to detect if text is code.

    Args:
        text: Text to check

    Returns:
        True if text appears to be code
    """
    code_indicators = [
        "def ",
        "class ",
        "import ",
        "from ",  # Python
        "function ",
        "const ",
        "let ",
        "var ",  # JavaScript
        "public ",
        "private ",
        "void ",  # Java/C++
        "<?php",
        "<?=",  # PHP
        "#include",
        "int main",  # C/C++
        "SELECT",
        "INSERT",
        "UPDATE",
        "FROM",
        "WHERE",
        "ORDER BY",  # SQL (case insensitive)
    ]

    # Check for common code patterns
    lines = text.split("\n")
    code_score = 0

    for line in lines[:20]:  # Check first 20 lines
        stripped = line.strip()
        stripped_upper = stripped.upper()

        # Check for code indicators
        for indicator in code_indicators:
            if indicator.upper() in stripped_upper:
                code_score += 2
                break

        # Check for indentation (common in code)
        if line and line[0] in " \t":
            code_score += 0.5

        # Check for brackets and semicolons
        if any(char in stripped for char in ["{", "}", ";", "()", "[]"]):
            code_score += 0.5

    # If score is high enough, likely code
    return code_score >= 3
