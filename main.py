#!/usr/bin/env python3
"""
Code Analyzer - Analyze code files using Gemma 3 270M AI model.

Usage:
    python main.py <file_path> [-q "question"]
    
Examples:
    python main.py /path/to/code.py
    python main.py /path/to/script.js -q "What does this function do?"
"""

import argparse
import os
import sys
import warnings
from pathlib import Path
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

def download_model():
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

def load_model(model_path):
    """Load the Gemma model with optimized settings."""
    try:
        # Detect if CUDA is available (for GPU support)
        n_gpu_layers = -1 if check_gpu_available() else 0
        
        llm = Llama(
            model_path=model_path,
            n_ctx=8192,  # Reduced for stability
            n_threads=min(4, os.cpu_count() or 4),  # Limit threads
            n_gpu_layers=n_gpu_layers,  # GPU layers if available
            verbose=False
        )
        return llm
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        sys.exit(1)

def check_gpu_available():
    """Check if CUDA GPU is available."""
    # Disabled for now - llama-cpp-python handles GPU automatically
    return False

def read_file(file_path):
    """Read the content of a code file."""
    try:
        path = Path(file_path).resolve()
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)
        
        if not path.is_file():
            print(f"❌ Not a file: {file_path}")
            sys.exit(1)
        
        # Check file size (limit to 100KB for safety)
        if path.stat().st_size > 100 * 1024:
            print(f"⚠️  Warning: Large file ({path.stat().st_size // 1024}KB). Only first 100KB will be analyzed.")
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(100 * 1024)
        else:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        
        return content, path.name
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)

def analyze_code(llm, code_content, filename, question):
    """Analyze code using the Gemma model."""
    # Truncate code if too long (keep under 20K chars for safety)
    if len(code_content) > 20000:
        code_content = code_content[:20000] + "\n... (truncated)"
    
    # Create a detailed prompt
    prompt = f"""<start_of_turn>user
Analyze the following code from file '{filename}':

{code_content}

{question}<end_of_turn>
<start_of_turn>model"""
    
    # Generate response
    try:
        output = llm(
            prompt,
            max_tokens=4096,
            temperature=0.3,  # Low temperature for accurate analysis
            top_p=0.95,
            top_k=40,
            repeat_penalty=1.1,
            echo=False,
            stop=["<end_of_turn>", "<eos>"]
        )
        
        return output['choices'][0]['text'].strip()
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return None

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Analyze code files using Gemma 3 270M AI model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s script.py
  %(prog)s /path/to/code.js -q "Find potential bugs"
  %(prog)s main.cpp -q "Suggest optimizations"
        """
    )
    
    parser.add_argument(
        'file_path',
        help='Path to the code file to analyze'
    )
    
    parser.add_argument(
        '-q', '--question',
        default=DEFAULT_QUESTION,
        help=f'Question about the code (default: "{DEFAULT_QUESTION}")'
    )
    
    parser.add_argument(
        '--no-gpu',
        action='store_true',
        help='Force CPU-only mode (disable GPU even if available)'
    )
    
    args = parser.parse_args()
    
    # Override GPU detection if requested
    if args.no_gpu:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    
    # Print header
    print("🔍 Code Analyzer powered by Gemma 3 270M")
    print("=" * 60)
    
    # Read the file
    code_content, filename = read_file(args.file_path)
    print(f"📄 Analyzing: {filename}")
    print(f"📏 File size: {len(code_content)} characters")
    
    # Download model if needed
    model_path = download_model()
    
    # Load model
    print("🤖 Loading AI model...")
    if not args.no_gpu and check_gpu_available():
        print("   Using GPU acceleration")
    else:
        print("   Using CPU mode")
    
    llm = load_model(model_path)
    print("✅ Model ready!\n")
    
    # Analyze the code
    print("🔎 Analyzing code...")
    print(f"❓ Question: {args.question}\n")
    print("-" * 60)
    
    response = analyze_code(llm, code_content, filename, args.question)
    
    if response:
        print("\n💡 Analysis Result:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        print("\n✨ Analysis complete!")
    else:
        print("\n❌ Analysis failed. Please try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()