"""
Core module for chi_llm - Zero Configuration Micro-LLM Library.
"""

import os
import warnings
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from threading import Lock
from llama_cpp import Llama
from huggingface_hub import hf_hub_download

# Suppress llama.cpp warnings
warnings.filterwarnings("ignore")
os.environ['LLAMA_CPP_LOG_LEVEL'] = 'ERROR'

# Model configuration
MODEL_REPO = "lmstudio-community/gemma-3-270m-it-GGUF"
MODEL_FILE = "gemma-3-270m-it-Q4_K_M.gguf"
MODEL_DIR = Path.home() / ".cache" / "chi_llm"

# Singleton pattern for model management
_model_instance = None
_model_lock = Lock()


class MicroLLM:
    """
    Zero-configuration micro LLM for your Python projects.
    
    Just import and use - no configuration needed!
    
    Example:
        >>> from chi_llm import MicroLLM
        >>> llm = MicroLLM()
        >>> response = llm.generate("Hello, how are you?")
        >>> print(response)
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        verbose: bool = False
    ):
        """
        Initialize MicroLLM with zero configuration.
        
        Args:
            model_path: Optional custom model path (auto-downloads if not provided)
            temperature: Creativity level (0.0 = deterministic, 1.0 = creative, default: 0.7)
            max_tokens: Maximum response length (default: 4096)
            verbose: Show model loading progress
        """
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.verbose = verbose
        self.model_path = model_path
        self._ensure_model_loaded()
    
    def _ensure_model_loaded(self):
        """Ensure the model is loaded using singleton pattern."""
        global _model_instance, _model_lock
        
        if _model_instance is None:
            with _model_lock:
                if _model_instance is None:
                    model_path = self.model_path or self._download_model()
                    _model_instance = self._load_model(model_path)
        
        self.llm = _model_instance
    
    def _download_model(self) -> str:
        """Download model if not cached (happens only once)."""
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model_path = MODEL_DIR / MODEL_FILE
        
        if model_path.exists():
            if self.verbose:
                print(f"✅ Using cached model from: {model_path}")
            return str(model_path)
        
        print(f"📥 First-time setup: Downloading model (~200MB)...")
        print(f"   This only happens once. Model will be cached in: {MODEL_DIR}")
        
        downloaded_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILE,
            local_dir=str(MODEL_DIR),
            resume_download=True
        )
        
        print("✅ Model ready! You won't see this message again.\n")
        return downloaded_path
    
    def _load_model(self, model_path: str) -> Llama:
        """Load the model with optimized settings."""
        try:
            if self.verbose:
                print("🤖 Loading model...")
            
            model = Llama(
                model_path=model_path,
                n_ctx=32768,  # Full model context
                n_threads=min(4, os.cpu_count() or 4),
                n_gpu_layers=0,  # CPU by default for maximum compatibility
                verbose=False
            )
            
            if self.verbose:
                print("✅ Model loaded successfully!")
            
            return model
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input text prompt
            **kwargs: Override default parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response
            
        Example:
            >>> llm.generate("Write a haiku about Python")
        """
        params = {
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'top_p': 0.95,
            'top_k': 40,
            'repeat_penalty': 1.1,
            'stop': ["<end_of_turn>", "<eos>", "\n\n\n"]
        }
        params.update(kwargs)
        
        # Format for Gemma model
        formatted_prompt = f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model"
        
        try:
            output = self.llm(formatted_prompt, echo=False, **params)
            return output['choices'][0]['text'].strip()
        except Exception as e:
            raise RuntimeError(f"Generation failed: {e}")
    
    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Chat conversation with context.
        
        Args:
            message: User message
            history: Optional conversation history
            
        Returns:
            AI response
            
        Example:
            >>> response = llm.chat("What's the weather like?")
            >>> response = llm.chat("And tomorrow?", history=[...])
        """
        conversation = ""
        
        if history:
            for turn in history:
                if 'user' in turn:
                    conversation += f"<start_of_turn>user\n{turn['user']}<end_of_turn>\n"
                if 'assistant' in turn:
                    conversation += f"<start_of_turn>model\n{turn['assistant']}<end_of_turn>\n"
        
        conversation += f"<start_of_turn>user\n{message}<end_of_turn>\n<start_of_turn>model"
        
        try:
            output = self.llm(
                conversation,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                echo=False,
                stop=["<end_of_turn>", "<eos>"]
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            raise RuntimeError(f"Chat failed: {e}")
    
    def complete(self, text: str, **kwargs) -> str:
        """
        Complete/continue the given text.
        
        Args:
            text: Text to complete
            **kwargs: Override parameters
            
        Returns:
            Completed text
            
        Example:
            >>> llm.complete("The quick brown fox")
        """
        # For completion, we use a simpler format
        try:
            output = self.llm(
                text,
                max_tokens=kwargs.get('max_tokens', 100),
                temperature=kwargs.get('temperature', 0.7),
                echo=False
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            raise RuntimeError(f"Completion failed: {e}")
    
    def ask(self, question: str, context: Optional[str] = None, **kwargs) -> str:
        """
        Ask a question, optionally with context.
        
        Args:
            question: Question to ask
            context: Optional context for the question
            **kwargs: Override parameters
            
        Returns:
            Answer to the question
            
        Example:
            >>> llm.ask("What is Python?")
            >>> llm.ask("What's the main function?", context=code_snippet)
        """
        if context:
            prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        else:
            prompt = f"Question: {question}\n\nAnswer:"
        
        return self.generate(prompt, **kwargs)
    
    def analyze(self, code: str, question: Optional[str] = None) -> str:
        """
        Analyze code (backward compatibility with CodeAnalyzer).
        
        Args:
            code: Code to analyze
            question: Optional specific question
            
        Returns:
            Analysis result
        """
        if not question:
            question = "Analyze this code and explain what it does"
        
        return self.ask(question, context=code)
    
    def extract(self, text: str, format: str = "json", schema: Optional[Dict] = None) -> str:
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
        """
        Summarize text.
        
        Args:
            text: Text to summarize
            max_sentences: Maximum sentences in summary
            
        Returns:
            Summary
            
        Example:
            >>> llm.summarize(long_article, max_sentences=2)
        """
        prompt = f"Summarize this text in {max_sentences} sentences:\n\n{text}\n\nSummary:"
        return self.generate(prompt, temperature=0.3)
    
    def translate(self, text: str, target_language: str = "English") -> str:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language
            
        Returns:
            Translated text
            
        Example:
            >>> llm.translate("Bonjour", "English")
        """
        prompt = f"Translate this text to {target_language}:\n\n{text}\n\nTranslation:"
        return self.generate(prompt, temperature=0.1)
    
    def classify(self, text: str, categories: List[str]) -> str:
        """
        Classify text into categories.
        
        Args:
            text: Text to classify
            categories: List of possible categories
            
        Returns:
            Best matching category
            
        Example:
            >>> llm.classify("I love this!", ["positive", "negative", "neutral"])
        """
        categories_str = ", ".join(categories)
        prompt = f"Classify this text into one of these categories [{categories_str}]:\n\n{text}\n\nCategory:"
        return self.generate(prompt, temperature=0.1, max_tokens=50)
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """
        Allow direct calling of the LLM.
        
        Example:
            >>> llm("Hello!")
        """
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