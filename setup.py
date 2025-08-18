#!/usr/bin/env python3
"""
Setup script for Code Analyzer - Gemma 3 270M powered code analysis tool.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")
else:
    long_description = "Code Analyzer - AI-powered code analysis using Gemma 3 270M"

setup(
    name="chi-llm",
    version="2.1.0",
    author="Jacek Jursza",
    description="Zero Configuration Micro-LLM Library - The simplest way to add AI to your Python project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jacekjursza/chi_llm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Minimal requirements - just the core LLM
        "llama-cpp-python>=0.2.0",
        "huggingface-hub>=0.20.0",
    ],
    extras_require={
        # Standard installation with config support
        "standard": [
            "pyyaml>=6.0",  # For YAML config files
        ],
        # Full installation with all features
        "full": [
            "pyyaml>=6.0",
            "sentence-transformers>=2.2.0",  # For embeddings
            "sqlite-vec>=0.1.0",  # Vector store in SQLite
            "numpy>=1.21.0",  # For vector operations
            "tqdm>=4.65.0",  # Progress bars
        ],
        # RAG-specific installation
        "rag": [
            "pyyaml>=6.0",
            "sentence-transformers>=2.2.0",
            "sqlite-vec>=0.1.0",
            "numpy>=1.21.0",
            "tqdm>=4.65.0",
        ],
        # GPU support
        "gpu": [
            "torch>=2.0.0",  # For GPU detection
        ],
        # Development dependencies
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "chi-llm=chi_llm.cli:main",
            "code-analyzer=chi_llm.cli:main",
            "gemma-analyze=chi_llm.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="llm ai ml nlp gemma local-llm zero-config micro-llm text-generation",
    project_urls={
        "Bug Reports": "https://github.com/jacekjursza/chi_llm/issues",
        "Source": "https://github.com/jacekjursza/chi_llm",
        "Documentation": "https://github.com/jacekjursza/chi_llm#readme",
    },
)