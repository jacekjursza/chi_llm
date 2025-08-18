@echo off
echo ============================================
echo Code Analyzer - Gemma 3 270M Installation
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv

echo [2/3] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/3] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ============================================
echo Installation complete!
echo ============================================
echo.
echo To use the analyzer:
echo   1. Activate environment: venv\Scripts\activate.bat
echo   2. Run: python main.py [file_path]
echo.
echo Example: python main.py test.py
echo.
pause