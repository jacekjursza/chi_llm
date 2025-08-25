"""
CLI entry composition and main() function.
"""

import argparse
import sys

from .cli_modules import register_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Chi_LLM - Zero Configuration Micro-LLM Library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version="chi_llm 2.1.0")
    parser.add_argument(
        "--tmp",
        action="store_true",
        help="Use project .chi_llm.tmp.json as config (sets CHI_LLM_CONFIG)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    register_all(subparsers)
    return parser


def main(argv=None):
    parser = build_parser()
    # First pass: allow global flags like --tmp to appear anywhere
    args_known, _ = parser.parse_known_args(argv)
    if getattr(args_known, "tmp", False):
        import os
        from pathlib import Path

        os.environ["CHI_LLM_CONFIG"] = str(Path.cwd() / ".chi_llm.tmp.json")
    # Remove global flag before final parse to avoid subparser complaining
    argv_list = list(argv) if argv is not None else None
    if argv_list is not None:
        argv_list = [a for a in argv_list if a != "--tmp"]
    args = parser.parse_args(argv_list)
    if not getattr(args, "command", None):
        parser.print_help()
        sys.exit(0)
    try:
        # If --tmp was requested, isolate env var to this invocation
        if getattr(args_known, "tmp", False):
            import os as _os

            key = "CHI_LLM_CONFIG"
            old = _os.environ.get(key)
            try:
                args.func(args)
            finally:
                if old is None:
                    _os.environ.pop(key, None)
                else:
                    _os.environ[key] = old
        else:
            args.func(args)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
