@echo off
REM chi_llm Universal Installer for Windows Batch
REM Simple batch version for older Windows systems

title chi_llm Installer
color 0B

echo.
echo      _____ _     _        _      _      __  __ 
echo     / ____^| ^|   ^(_^)      ^| ^|    ^| ^|    ^|  \/  ^|
echo    ^| ^|    ^| ^|__  _ ______^| ^|    ^| ^|    ^| \  / ^|
echo    ^| ^|    ^| '_ \^| ^|______^| ^|    ^| ^|    ^| ^|\/^| ^|
echo    ^| ^|____^| ^| ^| ^| ^|      ^| ^|____^| ^|____^| ^|  ^| ^|
echo     \_____^|_^| ^|_^|_^|      ^|______^|______^|_^|  ^|_^|
echo.
echo     Zero Configuration Micro-LLM Library
echo     https://github.com/jacekjursza/chi_llm
echo.

echo [INFO] Installing chi_llm...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3 is required but not installed.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Check if pip is installed
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is required but not installed.
    echo Please reinstall Python with pip included.
    pause
    exit /b 1
)

echo [OK] pip found

REM Install chi_llm
echo [INFO] Installing chi_llm from GitHub...
python -m pip install --user "git+https://github.com/jacekjursza/chi_llm.git"

if errorlevel 1 (
    echo [ERROR] Installation failed.
    echo Please check if you have git installed and try again.
    pause
    exit /b 1
)

REM Check if installation was successful
chi-llm --version >nul 2>&1
if errorlevel 1 (
    python -c "import chi_llm" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Installation failed. Please check the error messages above.
        pause
        exit /b 1
    ) else (
        echo [OK] chi_llm Python module installed successfully!
        echo [WARN] Command 'chi-llm' not in PATH. You can use: python -m chi_llm.cli
        echo [INFO] To use 'chi-llm' command, add Python Scripts to your PATH:
        echo   1. Open System Environment Variables
        echo   2. Add %%APPDATA%%\Python\Python3X\Scripts to PATH
        echo   3. Restart Command Prompt
    )
) else (
    echo [OK] chi-llm installed successfully!
    chi-llm --version
)

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Quick Start:
echo   # Run interactive setup (choose and download a model)
echo   chi-llm setup
echo.
echo   # Or start using immediately (downloads 200MB model first time)
echo   chi-llm generate "Write a Python hello world"
echo.
echo   # Interactive chat
echo   chi-llm chat
echo.
echo   # See all options
echo   chi-llm --help
echo.
echo Features:
echo   - 18+ curated models (270M to 9B, including Qwen3 with thinking mode)
echo   - 100%% local - no API keys needed
echo   - Zero configuration - works out of the box
echo   - Per-project configuration support
echo   - RAG support with SQLite vector store
echo.
echo Documentation: https://github.com/jacekjursza/chi_llm
echo Issues ^& Support: https://github.com/jacekjursza/chi_llm/issues
echo.
pause