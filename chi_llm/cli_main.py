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
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    register_all(subparsers)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        sys.exit(0)
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
