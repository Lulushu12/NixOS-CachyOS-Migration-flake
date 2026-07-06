"""Build the import graph of a modular flake config.

Entry points are discovered from flake.nix:
  * `./path.nix` references on lines mentioning `home-manager.users.*`
    become home-manager roots,
  * every other `./path.nix` reference becomes a system root
    (in practice: the host's default.nix inside the `modules = [ … ]` list).

From each root, `imports = [ … ];` blocks are followed recursively.
Disabled (commented-out) imports appear in the tree without children.
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import ConfigTree, ModuleFile, TreeNode
from .parser import parse_module

FLAKE_PATH_RE = re.compile(r"(?P<path>\./[\w./-]+\.nix)")
HOME_USER_RE = re.compile(r"home-manager\.users\.[\w-]+\s*=")


class ConfigError(Exception):
    pass


def find_flake_root(start: Path) -> Path:
    """Return the directory containing flake.nix, or raise ConfigError."""
    start = start.resolve()
    if start.is_file():
        start = start.parent
    candidates = [start, start / "nixos-config", *start.parents]
    for cand in candidates:
        if (cand / "flake.nix").is_file():
            return cand
    raise ConfigError(f"No flake.nix found at or above {start}")


def _flake_entry_points(flake: ModuleFile) -> tuple[list[Path], list[Path]]:
    system: list[Path] = []
    home: list[Path] = []
    for line in flake.lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for m in FLAKE_PATH_RE.finditer(stripped):
            resolved = (flake.path.parent / m.group("path")).resolve()
            if not resolved.exists():
                continue
            target = home if HOME_USER_RE.search(stripped) else system
            if resolved not in target:
                target.append(resolved)
    return system, home


def load_tree(root: Path) -> ConfigTree:
    root = find_flake_root(root)
    flake = parse_module(root / "flake.nix", root)
    system_paths, home_paths = _flake_entry_points(flake)

    cache: dict[Path, TreeNode] = {}

    def build(path: Path, kind: str, visiting: set[Path]) -> TreeNode:
        path = path.resolve()
        if path in cache:
            return cache[path]
        module = parse_module(path, root)
        node = TreeNode(file=module, kind=kind)
        cache[path] = node
        if module.imports_block:
            for entry in module.imports_block.entries:
                child: TreeNode | None = None
                if (
                    entry.enabled
                    and entry.resolved is not None
                    and entry.resolved not in visiting
                ):
                    child = build(entry.resolved, kind, visiting | {path})
                node.children.append((entry, child))
        return node

    tree = ConfigTree(root=root, flake=flake)
    for p in system_paths:
        tree.system_roots.append(build(p, "system", set()))
    for p in home_paths:
        tree.home_roots.append(build(p, "home", set()))
    if not tree.system_roots and not tree.home_roots:
        raise ConfigError(
            f"No module entry points found in {flake.path} — "
            "expected ./path.nix references in the flake outputs"
        )
    return tree
