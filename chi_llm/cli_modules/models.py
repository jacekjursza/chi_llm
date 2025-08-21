"""
Model management and setup commands.
"""

from argparse import _SubParsersAction

try:
    from ..models import ModelManager, MODELS, format_model_info
    from ..setup import SetupWizard

    HAS_MODELS = True
except Exception:  # pragma: no cover - optional
    HAS_MODELS = False


def cmd_setup(args):
    if not HAS_MODELS:
        print("❌ Model management not available")
        return
    wizard = SetupWizard()
    wizard.run()


def cmd_models(args):
    if not HAS_MODELS:
        print("❌ Model management not available")
        return
    manager = ModelManager()
    if args.models_command == "list":
        print("📦 Available Models:\n")
        current = manager.get_current_model()
        for model in MODELS.values():
            is_downloaded = manager.is_downloaded(model.id)
            is_current = model.id == current.id
            status = ""
            if is_current:
                status = " [CURRENT]"
            elif is_downloaded:
                status = " [Downloaded]"
            print(f"• {model.name} ({model.size}){status}")
            print(
                "  ID: "
                f"{model.id} | Size: {model.file_size_mb}MB | "
                f"RAM: {model.recommended_ram_gb}GB"
            )
            print(f"  {model.description}\n")
    elif args.models_command == "current":
        current = manager.get_current_model()
        stats = manager.get_model_stats()
        print(format_model_info(current, True, True))
        print(f"\n📁 Config source: {stats['config_source']}")
        print(f"   Path: {stats['config_path']}")
    elif args.models_command == "set":
        if args.model_id not in MODELS:
            print(f"❌ Unknown model: {args.model_id}")
            print("Available models:", ", ".join(MODELS.keys()))
            return
        if not manager.is_downloaded(args.model_id):
            print(f"⚠️  Model {args.model_id} is not downloaded.")
            print("Run 'chi-llm setup' to download it first.")
            return
        save_target = "local" if hasattr(args, "local") and args.local else "global"
        manager.set_default_model(args.model_id, save_target=save_target)
        model = MODELS[args.model_id]
        location = "locally" if save_target == "local" else "globally"
        print(f"✅ {model.name} is now the default model {location}!")
    elif args.models_command == "info":
        if args.model_id not in MODELS:
            print(f"❌ Unknown model: {args.model_id}")
            return
        model = MODELS[args.model_id]
        is_downloaded = manager.is_downloaded(args.model_id)
        is_current = args.model_id == manager.get_current_model().id
        print(format_model_info(model, is_downloaded, is_current))


def register(subparsers: _SubParsersAction):
    if not HAS_MODELS:
        return
    setup_parser = subparsers.add_parser("setup", help="Interactive model setup wizard")
    setup_parser.set_defaults(func=cmd_setup)

    models_parser = subparsers.add_parser("models", help="Model management")
    models_sub = models_parser.add_subparsers(
        dest="models_command", help="Model commands"
    )
    models_sub.add_parser("list", help="List all available models")
    models_sub.add_parser("current", help="Show current model")
    models_set = models_sub.add_parser("set", help="Set default model")
    models_set.add_argument("model_id", help="Model ID (e.g., phi3-mini, qwen3-1.7b)")
    models_set.add_argument(
        "--local", action="store_true", help="Save to local project config"
    )
    models_info = models_sub.add_parser("info", help="Show model details")
    models_info.add_argument("model_id", help="Model ID")
    models_parser.set_defaults(func=cmd_models)
