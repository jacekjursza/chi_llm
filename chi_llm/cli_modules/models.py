"""
Model management and setup commands.
"""

from argparse import _SubParsersAction
from importlib import resources
from typing import Any, Dict, List, Tuple

try:
    from ..models import ModelManager, MODELS
    from ..model_utils import format_model_info
    from ..setup import SetupWizard

    HAS_MODELS = True
except Exception:  # pragma: no cover - optional
    HAS_MODELS = False


def cmd_setup(args):
    if not HAS_MODELS:
        print("❌ Model management not available")
        return
    # Support subcommand: recommend
    if getattr(args, "setup_command", None) == "recommend":
        mgr = ModelManager()
        model = mgr.recommend_model()
        if getattr(args, "json", False):
            _print_json(
                {
                    "id": model.id,
                    "name": model.name,
                    "size": model.size,
                    "context_window": model.context_window,
                    "recommended_ram_gb": model.recommended_ram_gb,
                    "tags": model.tags,
                }
            )
        else:
            print("✅ Recommended model based on your system:\n")
            print(format_model_info(model))
        return
    # Default interactive wizard
    wizard = SetupWizard()
    wizard.run()


def _print_json(obj):
    import json

    print(json.dumps(obj, indent=2))


def _validate_models_yaml(path: str) -> Tuple[bool, Dict[str, Any]]:
    """Validate a models YAML catalog file.

    Returns (ok, report) where report contains errors, warnings, and stats.
    """
    report: Dict[str, Any] = {"errors": [], "warnings": [], "stats": {}}
    try:
        import yaml  # type: ignore
    except Exception:
        report["errors"].append("PyYAML not installed; install pyyaml to validate.")
        return False, report

    # Load YAML
    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
    except FileNotFoundError:
        report["errors"].append(f"File not found: {path}")
        return False, report
    except Exception as e:  # pragma: no cover - depends on file
        report["errors"].append(f"Failed to parse YAML: {e}")
        return False, report

    if not isinstance(doc, dict):
        report["errors"].append("Root must be a mapping/dict.")
        return False, report

    # Version (optional)
    ver = doc.get("version")
    if ver is not None and not isinstance(ver, (int, str)):
        report["warnings"].append("'version' should be int or string.")

    models = doc.get("models")
    if not isinstance(models, list) or not models:
        report["errors"].append("'models' must be a non-empty list.")
        return False, report

    ids: List[str] = []
    for i, item in enumerate(models):
        prefix = f"models[{i}]"
        if not isinstance(item, dict):
            report["errors"].append(f"{prefix}: entry must be a mapping/dict.")
            continue
        # Required minimal fields
        mid = item.get("id")
        repo = item.get("repo")
        filename = item.get("filename")
        if not mid:
            report["errors"].append(f"{prefix}: missing required field 'id'.")
        else:
            ids.append(str(mid))
        if not repo:
            report["errors"].append(f"{prefix} ({mid or '?' }): missing 'repo'.")
        if not filename:
            report["errors"].append(f"{prefix} ({mid or '?' }): missing 'filename'.")

        # Types and ranges
        if "file_size_mb" in item and not isinstance(
            item.get("file_size_mb"), (int, float)
        ):
            report["warnings"].append(
                f"{prefix} ({mid}): 'file_size_mb' should be number."
            )

        # context_window / context_windows
        ctx = item.get("context_window", item.get("context_windows"))
        if ctx is not None and not isinstance(ctx, int):
            report["errors"].append(f"{prefix} ({mid}): context_window should be int.")

        # recommended_ram_gb
        rg = item.get("recommended_ram_gb")
        if rg is not None and not isinstance(rg, (int, float)):
            report["errors"].append(
                f"{prefix} ({mid}): recommended_ram_gb should be number."
            )

        # tags
        tags = item.get("tags")
        if tags is not None and not isinstance(tags, list):
            report["errors"].append(f"{prefix} ({mid}): tags should be a list.")

        # New fields
        ngl = item.get("n_gpu_layers")
        if ngl is not None and (not isinstance(ngl, int) or ngl < 0):
            report["errors"].append(f"{prefix} ({mid}): n_gpu_layers must be int >= 0.")
        ot = item.get("output_tokens")
        if ot is not None and (not isinstance(ot, int) or ot <= 0):
            report["errors"].append(f"{prefix} ({mid}): output_tokens must be int > 0.")

    # Unique ids
    seen = set()
    dups = set()
    for mid in ids:
        if mid in seen:
            dups.add(mid)
        seen.add(mid)
    if dups:
        report["errors"].append(f"Duplicate model ids: {', '.join(sorted(dups))}")

    # zero_config_default
    zdef = doc.get("zero_config_default")
    if zdef is not None and zdef not in seen:
        report["errors"].append(
            f"zero_config_default '{zdef}' not present in models list."
        )

    report["stats"] = {"total_models": len(models)}
    return (len(report["errors"]) == 0), report


def cmd_models(args):
    if not HAS_MODELS:
        print("❌ Model management not available")
        return
    manager = ModelManager()
    if args.models_command == "list":
        if getattr(args, "json", False):
            current = manager.get_current_model().id
            out = []
            for m in MODELS.values():
                out.append(
                    {
                        "id": m.id,
                        "name": m.name,
                        "size": m.size,
                        "file_size_mb": m.file_size_mb,
                        "context_window": m.context_window,
                        "recommended_ram_gb": m.recommended_ram_gb,
                        "tags": m.tags,
                        "downloaded": manager.is_downloaded(m.id),
                        "current": m.id == current,
                    }
                )
            _print_json(out)
        else:
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
            # If an external provider is configured, show its local models too
            try:
                from ..utils import load_config
                from ..providers.discovery import list_provider_models

                cfg = load_config() or {}
                prov = cfg.get("provider") or {}
                ptype = prov.get("type")
                if ptype in {"lmstudio", "ollama"}:
                    plist = list_provider_models(prov)
                    print(f"🔌 Provider models ({ptype}):\n")
                    if not plist:
                        print("  (none or provider not reachable)\n")
                    else:
                        for pm in plist:
                            sz = f" [{pm['size']}]" if pm.get("size") else ""
                            print(f"• {pm['name']}{sz}")
                        print()
            except Exception:
                # Best-effort; ignore discovery errors in CLI
                pass
    elif args.models_command == "current":
        current = manager.get_current_model()
        stats = manager.get_model_stats()
        explain = getattr(args, "explain", False)
        # Compute effective model via ModelManager (single source of truth)
        prov_local_model = None
        try:
            from ..utils import load_config

            cfg = load_config() or {}
            prov = cfg.get("provider") or {}
            if prov.get("type") == "local":
                prov_local_model = prov.get("model")
        except Exception:
            pass
        effective_model, effective_note = manager.resolve_effective_model(
            provider_local_model=prov_local_model
        )
        if getattr(args, "json", False):
            out = {
                "id": current.id,
                "name": current.name,
                "size": current.size,
                "context_window": current.context_window,
                "downloaded": manager.is_downloaded(current.id),
                "config_source": stats.get("config_source"),
                "config_path": stats.get("config_path"),
                "available_ram_gb": stats.get("available_ram_gb"),
            }
            if explain:
                out["explain"] = {
                    "resolution_mode": stats.get("resolution_mode"),
                    "allow_global": stats.get("allow_global"),
                    "explicit_default": stats.get("explicit_default"),
                    "sources": stats.get("sources"),
                    "default_model": current.id,
                    "effective_model": effective_model,
                    "decision": effective_note,
                }
            _print_json(out)
        else:
            print(format_model_info(current, True, True))
            print(f"\n📁 Config source: {stats['config_source']}")
            print(f"   Path: {stats['config_path']}")
            if explain:
                print("\n🔎 Explain:")
                print(
                    "  • Resolution: {}, allow_global={}".format(
                        stats["resolution_mode"], stats["allow_global"]
                    )
                )
                print(
                    "  • Explicit default: {} (default_model={})".format(
                        stats["explicit_default"], current.id
                    )
                )
                srcs = stats.get("sources", {})
                print(
                    "  • Sources: env_cfg={} env_model={}".format(
                        srcs.get("env_cfg"), srcs.get("env_model")
                    )
                )
                print(
                    "             local={} project={} global={}".format(
                        srcs.get("local"), srcs.get("project"), srcs.get("global")
                    )
                )
                print(f"  • Effective model: {effective_model} ({effective_note})")
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
        if getattr(args, "json", False):
            _print_json(
                {
                    "id": model.id,
                    "name": model.name,
                    "size": model.size,
                    "file_size_mb": model.file_size_mb,
                    "context_window": model.context_window,
                    "n_gpu_layers": getattr(model, "n_gpu_layers", 0),
                    "output_tokens": getattr(model, "output_tokens", 4096),
                    "recommended_ram_gb": model.recommended_ram_gb,
                    "tags": model.tags,
                    "downloaded": is_downloaded,
                    "current": is_current,
                }
            )
        else:
            print(format_model_info(model, is_downloaded, is_current))
    elif args.models_command == "validate-yaml":
        # Determine path: user-given or package default
        path = getattr(args, "path", None)
        if not path:
            try:
                with resources.files("chi_llm").joinpath("models.yaml").open(
                    "r", encoding="utf-8"
                ) as f:
                    # Write to a temp file-like string for validation
                    import tempfile

                    with tempfile.NamedTemporaryFile(
                        "w+", delete=False, suffix=".yaml"
                    ) as tf:
                        tf.write(f.read())
                        path = tf.name
            except Exception:
                print(
                    "❌ Could not locate default models.yaml in package. "
                    "Provide a path."
                )
                return
        ok, report = _validate_models_yaml(path)
        if getattr(args, "json", False):
            _print_json({"ok": ok, **report, "path": path})
            return
        if ok:
            total = report["stats"].get("total_models", 0)
            print(f"✅ Valid models catalog ({total} models)")
        else:
            print("❌ Invalid models catalog")
            if report.get("errors"):
                print("Errors:")
                for e in report["errors"]:
                    print(f" - {e}")
        if report.get("warnings"):
            print("Warnings:")
            for w in report["warnings"]:
                print(f" - {w}")


def register(subparsers: _SubParsersAction):
    if not HAS_MODELS:
        return
    setup_parser = subparsers.add_parser("setup", help="Interactive model setup wizard")
    setup_sub = setup_parser.add_subparsers(dest="setup_command")
    # setup recommend --json
    setup_reco = setup_sub.add_parser(
        "recommend", help="Show recommended model for this system"
    )
    setup_reco.add_argument("--json", action="store_true", help="Output JSON")
    setup_parser.set_defaults(func=cmd_setup)

    models_parser = subparsers.add_parser("models", help="Model management")
    models_sub = models_parser.add_subparsers(
        dest="models_command", help="Model commands"
    )
    list_parser = models_sub.add_parser("list", help="List all available models")
    list_parser.add_argument(
        "--json", action="store_true", help="Output machine-readable JSON"
    )
    cur_parser = models_sub.add_parser("current", help="Show current model")
    cur_parser.add_argument(
        "--json", action="store_true", help="Output machine-readable JSON"
    )
    cur_parser.add_argument(
        "--explain",
        action="store_true",
        help="Show how the current model was chosen (with sources)",
    )
    models_set = models_sub.add_parser("set", help="Set default model")
    models_set.add_argument("model_id", help="Model ID (e.g., phi3-mini, qwen3-1.7b)")
    models_set.add_argument(
        "--local", action="store_true", help="Save to local project config"
    )
    models_info = models_sub.add_parser("info", help="Show model details")
    models_info.add_argument("model_id", help="Model ID")
    models_info.add_argument("--json", action="store_true", help="Output JSON")
    models_parser.set_defaults(func=cmd_models)

    v_yaml = models_sub.add_parser("validate-yaml", help="Validate a models YAML file")
    v_yaml.add_argument(
        "path", nargs="?", help="Path to models YAML (defaults to package file)"
    )
    v_yaml.add_argument("--json", action="store_true", help="Output JSON report")
