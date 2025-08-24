#!/usr/bin/env python3
"""
Interactive setup wizard for chi_llm.
Helps users download and configure models.
"""

import json
from pathlib import Path

from .models import ModelManager, MODELS
from .model_utils import format_model_info
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
            "header": "\033[95m",
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "bold": "\033[1m",
            "underline": "\033[4m",
            "end": "\033[0m",
        }

    def print_header(self):
        """Print welcome header."""
        print(
            f"""
{self.colors['header']}╔══════════════════════════════════════════════════════════════╗
║              🤖 Chi_LLM Model Setup Wizard 🤖                 ║
╚══════════════════════════════════════════════════════════════╝{self.colors['end']}

Welcome to chi_llm! Let's set up the perfect model for your system.
"""
        )

    def print_system_info(self):
        """Print system information."""
        stats = self.manager.get_model_stats()
        print(f"{self.colors['cyan']}📊 System Information:{self.colors['end']}")
        print(f"   Available RAM: {stats['available_ram_gb']:.1f}GB")
        print(f"   Models available: {stats['total_models']}")
        print(f"   Models downloaded: {stats['downloaded']}")
        print(f"   Current model: {stats['current_model']}")
        if stats["config_source"] != "default":
            print(
                f"   Config source: {stats['config_source']} ({stats['config_path']})"
            )
        print()

    def show_model_recommendations(self):
        """Show model recommendations based on system."""
        print(
            f"{self.colors['green']}💡 Recommendations based on your system:"
            f"{self.colors['end']}"
        )

        ram = self.manager._get_available_ram()

        if ram < 4:
            print("   Your system has limited RAM. Recommended models:")
            print("   • Gemma 270M - Ultra lightweight, runs on any system")
            print("   • Qwen3 1.7B - Best quality with thinking mode support")
        elif ram < 8:
            print("   Your system can run medium-sized models. Recommended:")
            print("   • Qwen3 1.7B - Excellent balance with thinking mode")
            print("   • Gemma 2 2B - Google's efficient 2B model")
            print("   • Phi-3 Mini - Best quality in 3.8B size")
        else:
            print("   Your system can run any model! Recommended:")
            print("   • Phi-3 Mini (3.8B) - Best overall quality")
            print("   • Qwen3 4B - Latest with 256K context window")
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
                ram_color = self.colors["red"]
            elif model.recommended_ram_gb > ram * 0.7:
                ram_color = self.colors["yellow"]
            else:
                ram_color = self.colors["green"]

            print(
                f"{i:2}. {self.colors['bold']}{model.name}{self.colors['end']}"
                f" ({model.size}){status}"
            )
            print(f"    {model.description}")
            print(
                f"    Size: {model.file_size_mb}MB | RAM: "
                f"{ram_color}{model.recommended_ram_gb}GB{self.colors['end']}"
            )
            print(f"    Context: {model.context_window:,}")
            print()

    def download_model(self, model_id: str) -> bool:
        """Download a model."""
        if not HAS_HF:
            print(
                f"{self.colors['red']}❌ huggingface-hub not installed!"
                f"{self.colors['end']}"
            )
            print("Please install with: pip install huggingface-hub")
            return False

        if model_id not in MODELS:
            print(
                f"{self.colors['red']}❌ Unknown model: {model_id}{self.colors['end']}"
            )
            return False

        model = MODELS[model_id]

        if self.manager.is_downloaded(model_id):
            print(
                f"{self.colors['yellow']}⚠️  Model {model.name} is already downloaded."
                f"{self.colors['end']}"
            )
            return True

        print(
            f"\n{self.colors['cyan']}📥 Downloading {model.name} "
            f"({model.file_size_mb}MB)...{self.colors['end']}"
        )
        print(f"   From: {model.repo}")
        print(f"   File: {model.filename}")

        try:
            MODEL_DIR.mkdir(parents=True, exist_ok=True)

            # Download with progress
            _ = hf_hub_download(
                repo_id=model.repo,
                filename=model.filename,
                local_dir=str(MODEL_DIR),
                resume_download=True,
            )

            self.manager.mark_downloaded(model_id)
            print(
                f"{self.colors['green']}✅ Successfully downloaded {model.name}!"
                f"{self.colors['end']}"
            )
            return True

        except Exception as e:
            print(f"{self.colors['red']}❌ Download failed: {e}{self.colors['end']}")
            return False

    def quick_setup(self):
        """Quick setup - download recommended model."""
        print(f"\n{self.colors['cyan']}⚡ Quick Setup{self.colors['end']}")

        recommended = self.manager.recommend_model()
        print(
            "Based on your system, we recommend: "
            f"{self.colors['bold']}{recommended.name}{self.colors['end']}"
        )
        print(f"Size: {recommended.file_size_mb}MB | {recommended.description}")

        response = input("\nDownload and set as default? (y/n): ").strip().lower()

        if response == "y":
            if self.download_model(recommended.id):
                self.manager.set_default_model(recommended.id)
                print(
                    f"{self.colors['green']}✅ {recommended.name} is now "
                    f"your default model!{self.colors['end']}"
                )
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

            if choice == "q":
                break

            elif choice == "d":
                # Show only downloaded models
                downloaded = [
                    m for m in MODELS.values() if self.manager.is_downloaded(m.id)
                ]
                if not downloaded:
                    print(
                        f"{self.colors['red']}No models downloaded yet!"
                        f"{self.colors['end']}"
                    )
                    continue

                print(f"\n{self.colors['cyan']}Downloaded models:{self.colors['end']}")
                for i, model in enumerate(downloaded, 1):
                    print(f"  {i}. {model.name} ({model.size})")

                try:
                    idx = int(input("Select model: ")) - 1
                    if 0 <= idx < len(downloaded):
                        self.manager.set_default_model(downloaded[idx].id)
                        print(
                            f"{self.colors['green']}✅ {downloaded[idx].name} "
                            f"is now default!{self.colors['end']}"
                        )
                except (ValueError, IndexError):
                    print(f"{self.colors['red']}Invalid selection!{self.colors['end']}")

            elif choice == "i":
                # Show detailed info
                model_num = input("Model number for info: ").strip()
                try:
                    idx = int(model_num) - 1
                    models = list(MODELS.values())
                    if 0 <= idx < len(models):
                        model = models[idx]
                        print(
                            format_model_info(
                                model,
                                self.manager.is_downloaded(model.id),
                                model.id == self.manager.get_current_model().id,
                            )
                        )
                except (ValueError, IndexError):
                    print(
                        f"{self.colors['red']}Invalid model number!{self.colors['end']}"
                    )

            elif choice.isdigit():
                # Download and set model
                try:
                    idx = int(choice) - 1
                    models = list(MODELS.values())
                    if 0 <= idx < len(models):
                        model = models[idx]
                        if self.download_model(model.id):
                            self.manager.set_default_model(model.id)
                            print(
                                f"{self.colors['green']}✅ {model.name} "
                                f"is now default!{self.colors['end']}"
                            )
                    else:
                        print(
                            f"{self.colors['red']}Invalid model number!"
                            f"{self.colors['end']}"
                        )
                except ValueError:
                    print(f"{self.colors['red']}Invalid input!{self.colors['end']}")

    def configure_rag_embeddings(self):
        """Configure RAG embedding models."""
        print(
            f"\n{self.colors['cyan']}🔍 RAG Embedding Configuration{self.colors['end']}"
        )
        print(
            "\nFastEmbed models are optimized ONNX models that run efficiently on CPU."
        )
        print("\nAvailable embedding models:")

        embedding_models = [
            (
                "intfloat/multilingual-e5-base",
                "280MB, 768 dims, 100+ languages (default)",
            ),
            ("BAAI/bge-small-en-v1.5", "34MB, 384 dims, English only (lightweight)"),
            ("BAAI/bge-base-en-v1.5", "110MB, 768 dims, English (balanced)"),
            ("BAAI/bge-large-en-v1.5", "335MB, 1024 dims, English (best quality)"),
            ("intfloat/multilingual-e5-small", "120MB, 384 dims, 100+ languages"),
            ("intfloat/multilingual-e5-large", "560MB, 1024 dims, 100+ languages"),
            ("nomic-ai/nomic-embed-text-v1.5", "140MB, 768 dims, 8192 tokens context"),
            ("jinaai/jina-embeddings-v2-base-en", "160MB, 768 dims, 8192 tokens"),
            ("Keep current", "No changes"),
        ]

        for i, (model, desc) in enumerate(embedding_models, 1):
            if i <= 4:  # First 4 are recommended
                print(
                    f"  {self.colors['green']}{i}. {model}{self.colors['end']} - {desc}"
                )
            else:
                print(f"  {i}. {model} - {desc}")

        choice = input("\nSelect embedding model (1-9): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(embedding_models) - 1:  # Not "Keep current"
                model_name = embedding_models[idx][0]
                # Save to config
                config_path = Path.home() / ".cache" / "chi_llm" / "rag_config.json"
                config_path.parent.mkdir(parents=True, exist_ok=True)

                config = {}
                if config_path.exists():
                    with open(config_path, "r") as f:
                        config = json.load(f)

                config["embedding_model"] = model_name

                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2)

                print(
                    f"{self.colors['green']}✅ RAG will use {model_name} for embeddings"
                    f"{self.colors['end']}"
                )
                print(f"Config saved to: {config_path}")

                # Check if fastembed is installed
                from importlib.util import find_spec

                if find_spec("fastembed") is None:
                    print(
                        f"\n{self.colors['yellow']}⚠️  FastEmbed not installed. "
                        f"Install with:{self.colors['end']}"
                    )
                    print("  pip install 'chi-llm[rag]'")
            elif idx == len(embedding_models) - 1:
                print("Configuration unchanged.")
            else:
                print(f"{self.colors['red']}Invalid selection!{self.colors['end']}")
        except (ValueError, IndexError):
            print(f"{self.colors['red']}Invalid input!{self.colors['end']}")

    def run(self):
        """Run the setup wizard."""
        self.print_header()
        self.print_system_info()
        self.show_model_recommendations()

        print(f"{self.colors['yellow']}Setup Options:{self.colors['end']}")
        print("  1. Quick setup (recommended model)")
        print("  2. Advanced setup (choose from all models)")
        print("  3. Configure RAG embeddings (optional)")
        print("  4. Show current configuration")
        print("  5. Exit")

        choice = input("\nYour choice (1-5): ").strip()

        if choice == "1":
            self.quick_setup()
        elif choice == "2":
            self.advanced_setup()
        elif choice == "3":
            self.configure_rag_embeddings()
        elif choice == "4":
            current = self.manager.get_current_model()
            print(f"\n{self.colors['cyan']}Current Configuration:{self.colors['end']}")
            print(format_model_info(current, True, True))
        elif choice == "5":
            print("Goodbye!")
        else:
            print(f"{self.colors['red']}Invalid choice!{self.colors['end']}")

        print(
            f"\n{self.colors['green']}Setup complete! You can always run "
            f"'chi-llm setup' to change models.{self.colors['end']}"
        )


def main():
    """Run setup wizard."""
    wizard = SetupWizard()
    wizard.run()


if __name__ == "__main__":
    main()
