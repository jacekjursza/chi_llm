"""
CLI modules registry for chi_llm.

Each module exposes a `register(subparsers)` function that
adds its subcommands to the given `argparse._SubParsersAction`.
"""

from . import basic, data, templates, rag, models, interactive, bootstrap


def register_all(subparsers):
    basic.register(subparsers)
    data.register(subparsers)
    templates.register(subparsers)
    rag.register(subparsers)
    models.register(subparsers)
    interactive.register(subparsers)
    bootstrap.register(subparsers)
