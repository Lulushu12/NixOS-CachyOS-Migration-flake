"""nixpkgs package search via the local `nix search` CLI.

Uses the flake's own nixpkgs pin when possible, so results match what a
rebuild would actually install. Falls back to the `nixpkgs` registry
alias. When nix isn't installed, `available()` is False and the UI should
offer free-text package entry instead of search.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

SEARCH_TIMEOUT = 180


@dataclass
class SearchResult:
    attr: str  # attribute path as used in package lists, e.g. `kdePackages.kdenlive`
    version: str
    description: str


def available() -> bool:
    return shutil.which("nix") is not None


def pinned_nixpkgs(flake_root: Path | None) -> str:
    """Flake ref of the config's locked nixpkgs, or the registry alias."""
    if flake_root is not None:
        lock = flake_root / "flake.lock"
        if lock.is_file():
            try:
                locked = json.loads(lock.read_text())["nodes"]["nixpkgs"]["locked"]
                if locked.get("type") == "github":
                    return f"github:{locked['owner']}/{locked['repo']}/{locked['rev']}"
            except (json.JSONDecodeError, KeyError):
                pass
    return "nixpkgs"


def search_nixpkgs(
    query: str, flake_root: Path | None = None, limit: int = 100
) -> list[SearchResult]:
    """Search nixpkgs for `query`. Raises RuntimeError on nix errors."""
    if not available():
        raise RuntimeError("nix is not installed")

    # Search the config's pinned nixpkgs so results match what a rebuild installs.
    cmd = [
        "nix", "search", pinned_nixpkgs(flake_root), query, "--json",
        "--extra-experimental-features", "nix-command flakes",
    ]
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True, timeout=SEARCH_TIMEOUT
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("nix search timed out") from exc
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "nix search failed")

    try:
        data = json.loads(res.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("could not parse nix search output") from exc

    results = []
    for key, info in data.items():
        # Keys look like `legacyPackages.x86_64-linux.kdePackages.kdenlive`.
        parts = key.split(".")
        attr = ".".join(parts[2:]) if parts[:1] == ["legacyPackages"] else key
        results.append(
            SearchResult(
                attr=attr,
                version=info.get("version", ""),
                description=info.get("description", ""),
            )
        )
        if len(results) >= limit:
            break
    return results
