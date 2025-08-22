# chi_llm Universal Installer for Windows PowerShell
# Usage: iwr -useb https://raw.githubusercontent.com/jacekjursza/chi_llm/master/install.ps1 | iex

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    Cyan = "Cyan"
    White = "White"
}

# Banner
Write-Host "     _____ _     _        _      _      __  __ " -ForegroundColor Cyan
Write-Host "    / ____| |   (_)      | |    | |    |  \/  |" -ForegroundColor Cyan
Write-Host "   | |    | |__  _ ______| |    | |    | \  / |" -ForegroundColor Cyan
Write-Host "   | |    | '_ \| |______| |    | |    | |\/| |" -ForegroundColor Cyan
Write-Host "   | |____| | | | |      | |____| |____| |  | |" -ForegroundColor Cyan
Write-Host "    \_____|_| |_|_|      |______|______|_|  |_|" -ForegroundColor Cyan
Write-Host "                                              " -ForegroundColor Cyan
Write-Host "    Zero Configuration Micro-LLM Library" -ForegroundColor Cyan
Write-Host "    https://github.com/jacekjursza/chi_llm" -ForegroundColor Cyan
Write-Host ""

Write-Host "🚀 Installing chi_llm..." -ForegroundColor Blue

# Check if Python is installed
try {
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ Python 3 is required but not installed." -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Parse Python version
$versionMatch = [regex]::Match($pythonVersion, "Python (\d+)\.(\d+)")
if ($versionMatch.Success) {
    $majorVersion = [int]$versionMatch.Groups[1].Value
    $minorVersion = [int]$versionMatch.Groups[2].Value
    $fullVersion = "$majorVersion.$minorVersion"
    
    if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 8)) {
        Write-Host "❌ Python 3.8+ is required. Found: $fullVersion" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host "✅ Python $fullVersion found" -ForegroundColor Green
} else {
    Write-Host "⚠️ Could not parse Python version, proceeding anyway..." -ForegroundColor Yellow
}

# Check if pip is installed
try {
    & python -m pip --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "pip not found"
    }
    Write-Host "✅ pip found" -ForegroundColor Green
} catch {
    Write-Host "❌ pip is required but not installed." -ForegroundColor Red
    Write-Host "Please reinstall Python with pip included." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Function to install chi_llm
function Install-ChiLLM {
    Write-Host "📦 Installing chi_llm from GitHub..." -ForegroundColor Blue
    
    try {
        # Try installing with python -m pip
        & python -m pip install --user "git+https://github.com/jacekjursza/chi_llm.git"
        if ($LASTEXITCODE -ne 0) {
            throw "Installation failed"
        }
    } catch {
        Write-Host "❌ Installation failed. Error: $_" -ForegroundColor Red
        Write-Host "Please check if you have git installed and try again." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Install chi_llm
Install-ChiLLM

# Check if installation was successful
try {
    & chi-llm --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $version = & chi-llm --version 2>$null
        Write-Host "✅ chi-llm installed successfully!" -ForegroundColor Green
        Write-Host "   Version: $version" -ForegroundColor Green
    } else {
        throw "Command not found"
    }
} catch {
    # Try importing the module
    try {
        & python -c "import chi_llm" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ chi_llm Python module installed successfully!" -ForegroundColor Green
            Write-Host "⚠️  Command 'chi-llm' not in PATH. You can use: python -m chi_llm.cli" -ForegroundColor Yellow
            Write-Host "💡 To use 'chi-llm' command, add Python Scripts to your PATH:" -ForegroundColor Yellow
            Write-Host "   1. Open System Environment Variables" -ForegroundColor Cyan
            Write-Host "   2. Add %APPDATA%\Python\Python3X\Scripts to PATH" -ForegroundColor Cyan
            Write-Host "   3. Restart PowerShell" -ForegroundColor Cyan
        } else {
            throw "Module import failed"
        }
    } catch {
        Write-Host "❌ Installation failed. Please check the error messages above." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "🎉 Installation complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick Start:" -ForegroundColor Blue
Write-Host "  # Run interactive setup (choose and download a model)" -ForegroundColor Green
Write-Host "  chi-llm setup" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Or start using immediately (downloads 200MB model first time)" -ForegroundColor Green
Write-Host "  chi-llm generate `"Write a Python hello world`"" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Interactive chat" -ForegroundColor Green
Write-Host "  chi-llm chat" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # See all options" -ForegroundColor Green
Write-Host "  chi-llm --help" -ForegroundColor Cyan
Write-Host ""
Write-Host "Features:" -ForegroundColor Blue
Write-Host "  🤖 18+ curated models (270M to 9B, including Qwen3 with thinking mode)"
Write-Host "  🏠 100% local - no API keys needed"
Write-Host "  ⚡ Zero configuration - works out of the box"
Write-Host "  📁 Per-project configuration support"
Write-Host "  🔍 RAG support with SQLite vector store"
Write-Host ""
Write-Host "Documentation: " -NoNewline -ForegroundColor Blue
Write-Host "https://github.com/jacekjursza/chi_llm" -ForegroundColor Cyan
Write-Host "Issues & Support: " -NoNewline -ForegroundColor Blue
Write-Host "https://github.com/jacekjursza/chi_llm/issues" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"