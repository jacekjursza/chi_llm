"""
CLI module for chi_llm package.
"""

import argparse
import os
import sys
from pathlib import Path
from .analyzer import CodeAnalyzer, DEFAULT_QUESTION


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
    
    try:
        # Create analyzer
        print("🤖 Loading AI model...")
        analyzer = CodeAnalyzer(use_gpu=not args.no_gpu)
        print("✅ Model ready!\n")
        
        # Analyze the file
        print(f"📄 Analyzing: {Path(args.file_path).name}")
        print("🔎 Analyzing code...")
        print(f"❓ Question: {args.question}\n")
        print("-" * 60)
        
        response = analyzer.analyze_file(args.file_path, args.question)
        
        print("\n💡 Analysis Result:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        print("\n✨ Analysis complete!")
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()