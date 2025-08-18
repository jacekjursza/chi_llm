"""
Analyzer module for backward compatibility.
This module wraps the new MicroLLM API to maintain compatibility with existing code.
"""

from typing import Optional
from pathlib import Path
from .core import MicroLLM, MODEL_REPO, MODEL_FILE, MODEL_DIR
from llama_cpp import Llama

# For backward compatibility
DEFAULT_QUESTION = "Describe what this code does and explain its main functionality."


class CodeAnalyzer:
    """
    A code analyzer using Gemma 3 270M model for AI-powered code analysis.
    
    DEPRECATED: This class is maintained for backward compatibility.
    Please use MicroLLM instead for new projects.
    
    Example:
        >>> from chi_llm import CodeAnalyzer
        >>> analyzer = CodeAnalyzer()
        >>> result = analyzer.analyze("def hello(): return 'world'")
        >>> print(result)
    """
    
    def __init__(self, model_path: Optional[str] = None, use_gpu: bool = True):
        """
        Initialize the CodeAnalyzer.
        
        Args:
            model_path: Optional path to a custom model file
            use_gpu: Whether to use GPU acceleration if available
        """
        # Use MicroLLM internally
        self._micro_llm = MicroLLM(model_path=model_path, verbose=False)
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.llm = self._micro_llm.llm
    
    def analyze(self, code: str, question: Optional[str] = None, 
                filename: Optional[str] = None) -> str:
        """
        Analyze code using the Gemma model.
        
        Args:
            code: The code to analyze
            question: Optional specific question about the code
            filename: Optional filename for context
            
        Returns:
            Analysis result as string
        """
        if not question:
            question = DEFAULT_QUESTION
        
        # Use MicroLLM's analyze method
        return self._micro_llm.analyze(code, question)
    
    def analyze_file(self, file_path: str, question: Optional[str] = None) -> str:
        """
        Analyze a code file.
        
        Args:
            file_path: Path to the file to analyze
            question: Optional specific question about the code
            
        Returns:
            Analysis result as string
        """
        path = Path(file_path).resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        
        # Check file size (limit to 100KB for safety)
        if path.stat().st_size > 100 * 1024:
            print(f"⚠️  Warning: Large file ({path.stat().st_size // 1024}KB). Only first 100KB will be analyzed.")
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(100 * 1024)
        else:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        
        return self.analyze(content, question)


# Convenience functions for backward compatibility
def load_model(model_path: str) -> Llama:
    """
    Load a Gemma model (for backward compatibility).
    
    DEPRECATED: Use MicroLLM instead.
    
    Args:
        model_path: Path to the model file
        
    Returns:
        Loaded Llama model instance
    """
    analyzer = CodeAnalyzer(model_path=model_path)
    return analyzer.llm


def analyze_code(llm: Llama, code_content: str, filename: str, question: str) -> str:
    """
    Analyze code using a loaded model (for backward compatibility).
    
    DEPRECATED: Use MicroLLM.analyze() instead.
    
    Args:
        llm: Loaded Llama model
        code_content: Code to analyze
        filename: Name of the file
        question: Question about the code
        
    Returns:
        Analysis result as string
    """
    from .core import MicroLLM
    micro_llm = MicroLLM()
    micro_llm.llm = llm
    return micro_llm.analyze(code_content, question)