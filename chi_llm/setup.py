#!/usr/bin/env python3
"""
Interactive setup wizard for chi_llm.
Helps users download and configure models.
"""

import sys
import os
from pathlib import Path
from typing import Optional, List
import time

from .models import ModelManager, MODELS, format_model_info, get_model_by_size
from .core import MODEL_DIR

try:
    from huggingface_hub import hf_hub_download
    HAS_HF = True
except ImportError:
    HAS_HF = False


class SetupWizard:
    """Interactive setup wizard for chi_llm."""
    
    def __init__(self):
        self.manager = ModelManager()
        self.colors = {
            'header': '\033[95m',
            'blue': '\033[94m',
            'cyan': '\033[96m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'bold': '\033[1m',
            'underline': '\033[4m',
            'end': '\033[0m'
        }
    
    def print_header(self):
        """Print welcome header."""
        print(f"""
{self.colors['header']}╔══════════════════════════════════════════════════════════════╗
║              🤖 Chi_LLM Model Setup Wizard 🤖                 ║
╚══════════════════════════════════════════════════════════════╝{self.colors['end']}

Welcome to chi_llm! Let's set up the perfect model for your system.
""")
    
    def print_system_info(self):
        """Print system information."""
        stats = self.manager.get_model_stats()
        print(f"{self.colors['cyan']}📊 System Information:{self.colors['end']}")
        print(f"   Available RAM: {stats['available_ram_gb']:.1f}GB")
        print(f"   Models available: {stats['total_models']}")
        print(f"   Models downloaded: {stats['downloaded']}")
        print(f"   Current model: {stats['current_model']}")
        if stats['config_source'] != 'default':
            print(f"   Config source: {stats['config_source']} ({stats['config_path']})")
        print()
    
    def show_model_recommendations(self):
        """Show model recommendations based on system."""
        print(f"{self.colors['green']}💡 Recommendations based on your system:{self.colors['end']}")
        
        ram = self.manager._get_available_ram()
        
        if ram < 4:
            print("   Your system has limited RAM. Recommended models:")
            print("   • Gemma 270M - Ultra lightweight, runs on any system")
            print("   • Qwen2 1.5B - Best quality for low-RAM systems")
        elif ram < 8:
            print("   Your system can run medium-sized models. Recommended:")
            print("   • Qwen2 1.5B - Excellent balance of size and quality")
            print("   • Gemma 2 2B - Google's efficient 2B model")
            print("   • Phi-3 Mini - Best quality in 3.8B size")
        else:
            print("   Your system can run any model! Recommended:")
            print("   • Phi-3 Mini (3.8B) - Best overall quality")
            print("   • Qwen2.5 3B - Latest with multilingual support")
            print("   • Gemma 2 9B (Q2) - Most powerful option")
        print()
    
    def list_models_menu(self):
        """Show models in a menu format."""
        print(f"{self.colors['blue']}📦 Available Models:{self.colors['end']}")
        
        models = self.manager.list_models(show_all=True)
        current_model = self.manager.get_current_model()
        
        for i, model in enumerate(models, 1):
            is_downloaded = self.manager.is_downloaded(model.id)
            is_current = model.id == current_model.id
            
            status = ""
            if is_current:
                status = f" {self.colors['green']}[CURRENT]{self.colors['end']}"
            elif is_downloaded:
                status = f" {self.colors['cyan']}[Downloaded]{self.colors['end']}"
            
            # Show size and RAM requirement with color coding
            ram = self.manager._get_available_ram()
            if model.recommended_ram_gb > ram:
                ram_color = self.colors['red']
            elif model.recommended_ram_gb > ram * 0.7:
                ram_color = self.colors['yellow']
            else:
                ram_color = self.colors['green']
            
            print(f"{i:2}. {self.colors['bold']}{model.name}{self.colors['end']} ({model.size}){status}")
            print(f"    {model.description}")
            print(f"    Size: {model.file_size_mb}MB | RAM: {ram_color}{model.recommended_ram_gb}GB{self.colors['end']} | Context: {model.context_window:,}")
            print()
    
    def download_model(self, model_id: str) -> bool:
        """Download a model."""
        if not HAS_HF:
            print(f"{self.colors['red']}❌ huggingface-hub not installed!{self.colors['end']}")
            print("Please install with: pip install huggingface-hub")
            return False
        
        if model_id not in MODELS:
            print(f"{self.colors['red']}❌ Unknown model: {model_id}{self.colors['end']}")
            return False
        
        model = MODELS[model_id]
        
        if self.manager.is_downloaded(model_id):
            print(f"{self.colors['yellow']}⚠️  Model {model.name} is already downloaded.{self.colors['end']}")
            return True
        
        print(f"\n{self.colors['cyan']}📥 Downloading {model.name} ({model.file_size_mb}MB)...{self.colors['end']}")
        print(f"   From: {model.repo}")
        print(f"   File: {model.filename}")
        
        try:
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            
            # Download with progress
            downloaded_path = hf_hub_download(
                repo_id=model.repo,
                filename=model.filename,
                local_dir=str(MODEL_DIR),
                resume_download=True
            )
            
            self.manager.mark_downloaded(model_id)
            print(f"{self.colors['green']}✅ Successfully downloaded {model.name}!{self.colors['end']}")
            return True
            
        except Exception as e:
            print(f"{self.colors['red']}❌ Download failed: {e}{self.colors['end']}")
            return False
    
    def quick_setup(self):
        """Quick setup - download recommended model."""
        print(f"\n{self.colors['cyan']}⚡ Quick Setup{self.colors['end']}")
        
        recommended = self.manager.recommend_model()
        print(f"Based on your system, we recommend: {self.colors['bold']}{recommended.name}{self.colors['end']}")
        print(f"Size: {recommended.file_size_mb}MB | {recommended.description}")
        
        response = input(f"\nDownload and set as default? (y/n): ").strip().lower()
        
        if response == 'y':
            if self.download_model(recommended.id):
                self.manager.set_default_model(recommended.id)
                print(f"{self.colors['green']}✅ {recommended.name} is now your default model!{self.colors['end']}")
                return True
        
        return False
    
    def advanced_setup(self):
        """Advanced setup - choose from all models."""
        print(f"\n{self.colors['cyan']}🔧 Advanced Setup{self.colors['end']}")
        
        while True:
            self.list_models_menu()
            
            print(f"{self.colors['yellow']}Options:{self.colors['end']}")
            print("  1-9: Download and set model as default")
            print("  d:   Set already downloaded model as default")
            print("  i:   Show detailed model info")
            print("  q:   Quit setup")
            
            choice = input("\nYour choice: ").strip().lower()
            
            if choice == 'q':
                break
            
            elif choice == 'd':
                # Show only downloaded models
                downloaded = [m for m in MODELS.values() if self.manager.is_downloaded(m.id)]
                if not downloaded:
                    print(f"{self.colors['red']}No models downloaded yet!{self.colors['end']}")
                    continue
                
                print(f"\n{self.colors['cyan']}Downloaded models:{self.colors['end']}")
                for i, model in enumerate(downloaded, 1):
                    print(f"  {i}. {model.name} ({model.size})")
                
                try:
                    idx = int(input("Select model: ")) - 1
                    if 0 <= idx < len(downloaded):
                        self.manager.set_default_model(downloaded[idx].id)
                        print(f"{self.colors['green']}✅ {downloaded[idx].name} is now default!{self.colors['end']}")
                except (ValueError, IndexError):
                    print(f"{self.colors['red']}Invalid selection!{self.colors['end']}")
            
            elif choice == 'i':
                # Show detailed info
                model_num = input("Model number for info: ").strip()
                try:
                    idx = int(model_num) - 1
                    models = list(MODELS.values())
                    if 0 <= idx < len(models):
                        model = models[idx]
                        print(format_model_info(
                            model,
                            self.manager.is_downloaded(model.id),
                            model.id == self.manager.get_current_model().id
                        ))
                except (ValueError, IndexError):
                    print(f"{self.colors['red']}Invalid model number!{self.colors['end']}")
            
            elif choice.isdigit():
                # Download and set model
                try:
                    idx = int(choice) - 1
                    models = list(MODELS.values())
                    if 0 <= idx < len(models):
                        model = models[idx]
                        if self.download_model(model.id):
                            self.manager.set_default_model(model.id)
                            print(f"{self.colors['green']}✅ {model.name} is now default!{self.colors['end']}")
                    else:
                        print(f"{self.colors['red']}Invalid model number!{self.colors['end']}")
                except ValueError:
                    print(f"{self.colors['red']}Invalid input!{self.colors['end']}")
    
    def run(self):
        """Run the setup wizard."""
        self.print_header()
        self.print_system_info()
        self.show_model_recommendations()
        
        print(f"{self.colors['yellow']}Setup Options:{self.colors['end']}")
        print("  1. Quick setup (recommended model)")
        print("  2. Advanced setup (choose from all models)")
        print("  3. Show current configuration")
        print("  4. Exit")
        
        choice = input("\nYour choice (1-4): ").strip()
        
        if choice == '1':
            self.quick_setup()
        elif choice == '2':
            self.advanced_setup()
        elif choice == '3':
            current = self.manager.get_current_model()
            print(f"\n{self.colors['cyan']}Current Configuration:{self.colors['end']}")
            print(format_model_info(current, True, True))
        elif choice == '4':
            print("Goodbye!")
        else:
            print(f"{self.colors['red']}Invalid choice!{self.colors['end']}")
        
        print(f"\n{self.colors['green']}Setup complete! You can always run 'chi-llm setup' to change models.{self.colors['end']}")


def main():
    """Run setup wizard."""
    wizard = SetupWizard()
    wizard.run()


if __name__ == "__main__":
    main()