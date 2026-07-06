"""Command-line entry point: locate the flake and launch the TUI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core.graph import ConfigError, find_flake_root

DEFAULT_SEARCH = [Path.cwd(), Path("/etc/nixos")]


def locate_config(arg: str | None) -> Path:
    if arg is not None:
        return find_flake_root(Path(arg))
    errors = []
    for candidate in DEFAULT_SEARCH:
        try:
            return find_flake_root(candidate)
        except ConfigError as exc:
            errors.append(str(exc))
    raise ConfigError(
        "Could not find a flake.nix. Pass the config path explicitly:\n"
        "  nixcfg /path/to/config\n" + "\n".join(errors)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nixcfg",
        description="Visual browser and editor for a modular NixOS flake config",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="path to the config (a flake.nix, its directory, or any dir below it); "
        "defaults to the current directory, then /etc/nixos",
    )
    parser.add_argument(
        "--no-validate", action="store_true",
        help="skip `nix flake check` when applying changes",
    )
    parser.add_argument(
        "--no-commit", action="store_true",
        help="don't git-commit applied changes",
    )
    args = parser.parse_args(argv)

    try:
        root = locate_config(args.path)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    from .tui.app import NixcfgApp

    app = NixcfgApp(
        root=root, validate=not args.no_validate, commit=not args.no_commit
    )
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
