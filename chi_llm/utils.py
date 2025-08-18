"""
Utility functions for chi_llm.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or environment.
    
    Looks for config in this order:
    1. Provided config_path
    2. .chi_llm.yaml in current directory
    3. .chi_llm.json in current directory
    4. CHI_LLM_CONFIG environment variable
    5. Default configuration
    
    Returns:
        Configuration dictionary
    """
    # Default configuration
    default_config = {
        "model": {
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.95,
            "top_k": 40
        },
        "cache_dir": str(Path.home() / ".cache" / "chi_llm"),
        "verbose": False
    }
    
    # Try provided path
    if config_path and Path(config_path).exists():
        return _load_file_config(config_path, default_config)
    
    # Try current directory
    for filename in [".chi_llm.yaml", ".chi_llm.yml", ".chi_llm.json"]:
        if Path(filename).exists():
            return _load_file_config(filename, default_config)
    
    # Try environment variable
    env_config = os.environ.get("CHI_LLM_CONFIG")
    if env_config:
        if Path(env_config).exists():
            return _load_file_config(env_config, default_config)
        else:
            # Try parsing as JSON
            try:
                config = json.loads(env_config)
                return {**default_config, **config}
            except json.JSONDecodeError:
                pass
    
    return default_config


def _load_file_config(filepath: str, defaults: Dict) -> Dict[str, Any]:
    """Load configuration from file."""
    path = Path(filepath)
    
    try:
        if path.suffix in ['.yaml', '.yml']:
            with open(path, 'r') as f:
                config = yaml.safe_load(f) or {}
        elif path.suffix == '.json':
            with open(path, 'r') as f:
                config = json.load(f)
        else:
            # Try to detect format
            with open(path, 'r') as f:
                content = f.read()
                try:
                    config = json.loads(content)
                except:
                    config = yaml.safe_load(content) or {}
        
        # Merge with defaults
        return {**defaults, **config}
    except Exception as e:
        print(f"Warning: Could not load config from {filepath}: {e}")
        return defaults


def truncate_text(text: str, max_length: int = 20000, suffix: str = "\n... (truncated)") -> str:
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
    
    return text[:max_length - len(suffix)] + suffix


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
            formatted.append(f"<start_of_turn>model\n{message['assistant']}<end_of_turn>")
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
    error_patterns = [
        "error:",
        "failed to",
        "could not",
        "unable to"
    ]
    
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
        "[END]",
        "[DONE]"
    ]
    
    for artifact in artifacts:
        response = response.replace(artifact, "")
    
    return response.strip()


def split_into_chunks(text: str, chunk_size: int = 15000, overlap: int = 500) -> List[str]:
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
            for sep in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
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
        "size_mb": 200
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
        'def ', 'class ', 'import ', 'from ',  # Python
        'function ', 'const ', 'let ', 'var ',  # JavaScript
        'public ', 'private ', 'void ',  # Java/C++
        '<?php', '<?=',  # PHP
        '#include', 'int main',  # C/C++
        'SELECT ', 'INSERT ', 'UPDATE ',  # SQL
    ]
    
    # Check for common code patterns
    lines = text.split('\n')
    code_score = 0
    
    for line in lines[:20]:  # Check first 20 lines
        stripped = line.strip()
        
        # Check for code indicators
        for indicator in code_indicators:
            if indicator in stripped:
                code_score += 2
                break
        
        # Check for indentation (common in code)
        if line and line[0] in ' \t':
            code_score += 0.5
        
        # Check for brackets and semicolons
        if any(char in stripped for char in ['{', '}', ';', '()', '[]']):
            code_score += 0.5
    
    # If score is high enough, likely code
    return code_score >= 5