"""
Core analyzer module for chi_llm package.
"""

import os
import warnings
from pathlib import Path
from typing import Optional, Tuple
from llama_cpp import Llama
from huggingface_hub import hf_hub_download

# Suppress llama.cpp warnings
warnings.filterwarnings("ignore")
os.environ['LLAMA_CPP_LOG_LEVEL'] = 'ERROR'

# Model configuration
MODEL_REPO = "lmstudio-community/gemma-3-270m-it-GGUF"
MODEL_FILE = "gemma-3-270m-it-Q4_K_M.gguf"
MODEL_DIR = Path.home() / ".cache" / "gemma_analyzer"
DEFAULT_QUESTION = "Describe what this code does and explain its main functionality."


class CodeAnalyzer:
    """
    A code analyzer using Gemma 3 270M model for AI-powered code analysis.
    
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
        self.model_path = model_path or self._download_model()
        self.use_gpu = use_gpu
        self.llm = None
        self._load_model()
    
    def _download_model(self) -> str:
        """Download the GGUF model from HuggingFace if not cached."""
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model_path = MODEL_DIR / MODEL_FILE
        
        if model_path.exists():
            return str(model_path)
        
        print(f"📥 Downloading model (one-time setup, ~200MB)...")
        print(f"   Model will be cached in: {MODEL_DIR}")
        
        downloaded_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILE,
            local_dir=str(MODEL_DIR),
            resume_download=True
        )
        
        print("✅ Model downloaded successfully!\n")
        return downloaded_path
    
    def _load_model(self):
        """Load the Gemma model with optimized settings."""
        try:
            # GPU support disabled by default for stability
            n_gpu_layers = 0
            
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=8192,
                n_threads=min(4, os.cpu_count() or 4),
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
        except Exception as e:
            raise RuntimeError(f"Error loading model: {e}")
    
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
        
        if not filename:
            filename = "code"
        
        # Truncate code if too long (keep under 20K chars for safety)
        if len(code) > 20000:
            code = code[:20000] + "\n... (truncated)"
        
        # Create a detailed prompt
        prompt = f"""<start_of_turn>user
Analyze the following code from file '{filename}':

{code}

{question}<end_of_turn>
<start_of_turn>model"""
        
        # Generate response
        try:
            output = self.llm(
                prompt,
                max_tokens=4096,
                temperature=0.3,
                top_p=0.95,
                top_k=40,
                repeat_penalty=1.1,
                echo=False,
                stop=["<end_of_turn>", "<eos>"]
            )
            
            return output['choices'][0]['text'].strip()
        except Exception as e:
            raise RuntimeError(f"Error during analysis: {e}")
    
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
        
        return self.analyze(content, question, path.name)


# Convenience functions for backward compatibility
def load_model(model_path: str) -> Llama:
    """
    Load a Gemma model (for backward compatibility).
    
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
    
    Args:
        llm: Loaded Llama model
        code_content: Code to analyze
        filename: Name of the file
        question: Question about the code
        
    Returns:
        Analysis result as string
    """
    # Create temporary analyzer with the provided model
    analyzer = CodeAnalyzer()
    analyzer.llm = llm
    return analyzer.analyze(code_content, question, filename)