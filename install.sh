#!/bin/bash
# chi_llm Universal Installer for Linux/macOS
# Usage: curl -sSL https://raw.githubusercontent.com/jacekjursza/chi_llm/master/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
cat << "EOF"
     _____ _     _        _      _      __  __ 
    / ____| |   (_)      | |    | |    |  \/  |
   | |    | |__  _ ______| |    | |    | \  / |
   | |    | '_ \| |______| |    | |    | |\/| |
   | |____| | | | |      | |____| |____| |  | |
    \_____|_| |_|_|      |______|______|_|  |_|
                                              
    Zero Configuration Micro-LLM Library
    https://github.com/jacekjursza/chi_llm
EOF
echo -e "${NC}"

echo -e "${BLUE}🚀 Installing chi_llm...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
    echo -e "Please install Python 3.8+ first:"
    echo -e "  Ubuntu/Debian: ${YELLOW}sudo apt update && sudo apt install python3 python3-pip${NC}"
    echo -e "  CentOS/RHEL:   ${YELLOW}sudo yum install python3 python3-pip${NC}"
    echo -e "  macOS:         ${YELLOW}brew install python3${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python 3.8+ is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo -e "${RED}❌ pip is required but not installed.${NC}"
    echo -e "Please install pip first:"
    echo -e "  Ubuntu/Debian: ${YELLOW}sudo apt install python3-pip${NC}"
    echo -e "  macOS:         ${YELLOW}python3 -m ensurepip --upgrade${NC}"
    exit 1
fi

echo -e "${GREEN}✅ pip found${NC}"

# Function to install chi_llm
install_chi_llm() {
    echo -e "${BLUE}📦 Installing chi_llm from GitHub...${NC}"
    
    # Try with pip3 first, then fallback to python3 -m pip
    if command -v pip3 &> /dev/null; then
        pip3 install --user "git+https://github.com/jacekjursza/chi_llm.git" || {
            echo -e "${YELLOW}⚠️  pip3 failed, trying python3 -m pip...${NC}"
            python3 -m pip install --user "git+https://github.com/jacekjursza/chi_llm.git"
        }
    else
        python3 -m pip install --user "git+https://github.com/jacekjursza/chi_llm.git"
    fi
}

# Install chi_llm
install_chi_llm

# Check if installation was successful
if command -v chi-llm &> /dev/null; then
    echo -e "${GREEN}✅ chi-llm installed successfully!${NC}"
    CHI_LLM_VERSION=$(chi-llm --version 2>/dev/null || echo "unknown")
    echo -e "${GREEN}   Version: $CHI_LLM_VERSION${NC}"
elif python3 -c "import chi_llm" 2>/dev/null; then
    echo -e "${GREEN}✅ chi_llm Python module installed successfully!${NC}"
    echo -e "${YELLOW}⚠️  Command 'chi-llm' not in PATH. You can use: python3 -m chi_llm.cli${NC}"
    
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo -e "${YELLOW}💡 To use 'chi-llm' command, add ~/.local/bin to your PATH:${NC}"
        echo -e "   ${CYAN}echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc${NC}"
        echo -e "   ${CYAN}source ~/.bashrc${NC}"
    fi
else
    echo -e "${RED}❌ Installation failed. Please check the error messages above.${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}🎉 Installation complete!${NC}"
echo ""
echo -e "${BLUE}Quick Start:${NC}"
echo -e "  ${GREEN}# Run interactive setup (choose and download a model)${NC}"
echo -e "  ${CYAN}chi-llm setup${NC}"
echo ""
echo -e "  ${GREEN}# Or start using immediately (downloads 200MB model first time)${NC}"
echo -e "  ${CYAN}chi-llm generate \"Write a Python hello world\"${NC}"
echo ""
echo -e "  ${GREEN}# Interactive chat${NC}"
echo -e "  ${CYAN}chi-llm chat${NC}"
echo ""
echo -e "  ${GREEN}# See all options${NC}"
echo -e "  ${CYAN}chi-llm --help${NC}"
echo ""
echo -e "${BLUE}Features:${NC}"
echo -e "  🤖 9 curated models (270M to 9B parameters)"
echo -e "  🏠 100% local - no API keys needed"
echo -e "  ⚡ Zero configuration - works out of the box"
echo -e "  📁 Per-project configuration support"
echo -e "  🔍 RAG support with SQLite vector store"
echo ""
echo -e "${BLUE}Documentation:${NC} ${CYAN}https://github.com/jacekjursza/chi_llm${NC}"
echo -e "${BLUE}Issues & Support:${NC} ${CYAN}https://github.com/jacekjursza/chi_llm/issues${NC}"