"""Thin wrapper for CLI entrypoint (modularized)."""

from .cli_main import main  # re-export

if __name__ == "__main__":  # pragma: no cover
    main()
