#!/bin/bash

echo "============================================"
echo "Code Analyzer - Gemma 3 270M Installation"
echo "============================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python $python_version"

# Create virtual environment
echo "[1/3] Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "[2/3] Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "[3/3] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "============================================"
echo "Installation complete!"
echo "============================================"
echo
echo "To use the analyzer:"
echo "  1. Activate environment: source venv/bin/activate"
echo "  2. Run: python main.py [file_path]"
echo
echo "Example: python main.py test.py"
echo
echo "Optional: Install with GPU support"
echo "  pip install torch"
echo