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
    name="code-analyzer-gemma",
    version="1.0.0",
    author="AI Assistant",
    description="Analyze code files using Gemma 3 270M AI model",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/code-analyzer-gemma",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Documentation",
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
        "llama-cpp-python>=0.2.0",
        "huggingface-hub>=0.20.0",
    ],
    extras_require={
        "gpu": [
            "torch>=2.0.0",  # For GPU detection
        ],
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "code-analyzer=main:main",
            "gemma-analyze=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    project_urls={
        "Bug Reports": "https://github.com/yourusername/code-analyzer-gemma/issues",
        "Source": "https://github.com/yourusername/code-analyzer-gemma",
    },
)