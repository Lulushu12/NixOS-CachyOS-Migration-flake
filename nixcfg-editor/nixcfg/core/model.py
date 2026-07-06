"""Data model for a parsed modular NixOS flake configuration.

Everything here is a plain dataclass produced by `parser` / `graph` and
consumed by `edits` and the UI. Line numbers are 0-based indexes into
`ModuleFile.lines`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SectionInfo:
    """A `# ── Title ──…` header inside a package list."""

    title: str
    line: int


@dataclass
class PackageEntry:
    """One entry of a package list.

    `name` is the attribute path (e.g. `kdePackages.kdenlive`) or, for
    parenthesized expressions, the full raw expression text.
    """

    name: str
    comment: str | None
    enabled: bool
    line: int
    end_line: int
    is_expr: bool
    section: str | None

    @property
    def display_name(self) -> str:
        if not self.is_expr:
            return self.name
        # Compact a multi-line expression to something list-friendly.
        text = " ".join(self.name.split())
        return text if len(text) <= 60 else text[:57] + "..."


@dataclass
class PackageList:
    """A `<attrpath> = with pkgs; [ … ];` list inside a module file."""

    attrpath: str
    start_line: int  # line containing the opening '['
    end_line: int  # line containing the closing '];'
    with_pkgs: bool
    sections: list[SectionInfo] = field(default_factory=list)
    packages: list[PackageEntry] = field(default_factory=list)

    @property
    def is_primary(self) -> bool:
        """The lists the add-package flow targets by default."""
        return self.attrpath in ("environment.systemPackages", "home.packages")


@dataclass
class ImportEntry:
    """One entry of an `imports = [ … ];` block. Disabled == commented out."""

    raw: str  # the path text as written, e.g. ../../modules/vm.nix
    resolved: Path | None  # absolute path if the file exists
    comment: str | None
    enabled: bool
    line: int


@dataclass
class ImportsBlock:
    start_line: int
    end_line: int
    entries: list[ImportEntry] = field(default_factory=list)


@dataclass
class OptionEntry:
    """A `some.attr.path = value;` assignment (best-effort, for display).

    `simple` marks scalar values (bool / string / int) that a future
    version can edit through the UI; everything else is display-only.
    """

    attrpath: str
    value: str
    line: int
    simple: bool


@dataclass
class ModuleFile:
    path: Path
    rel: str  # path relative to the config root, for display
    lines: list[str]
    header_comment: str  # leading comment block, used as the description
    imports_block: ImportsBlock | None
    package_lists: list[PackageList]
    options: list[OptionEntry]
    read_only: bool

    @property
    def text(self) -> str:
        return "\n".join(self.lines) + "\n"

    def primary_package_lists(self) -> list[PackageList]:
        return [pl for pl in self.package_lists if pl.is_primary]


@dataclass
class TreeNode:
    """A module file plus its resolved children, forming the import graph."""

    file: ModuleFile
    kind: str  # 'system' | 'home'
    # (import entry, child node). Child is None when the import is disabled
    # or the file is missing.
    children: list[tuple[ImportEntry, "TreeNode | None"]] = field(default_factory=list)


@dataclass
class ConfigTree:
    root: Path  # directory containing flake.nix
    flake: ModuleFile
    system_roots: list[TreeNode] = field(default_factory=list)
    home_roots: list[TreeNode] = field(default_factory=list)

    def all_nodes(self) -> list[TreeNode]:
        """Every reachable node, depth-first, system tree then home tree."""
        out: list[TreeNode] = []
        seen: set[Path] = set()

        def walk(node: TreeNode) -> None:
            if node.file.path in seen:
                return
            seen.add(node.file.path)
            out.append(node)
            for _, child in node.children:
                if child is not None:
                    walk(child)

        for root in self.system_roots + self.home_roots:
            walk(root)
        return out

    def find(self, path: Path) -> TreeNode | None:
        for node in self.all_nodes():
            if node.file.path == path:
                return node
        return None
