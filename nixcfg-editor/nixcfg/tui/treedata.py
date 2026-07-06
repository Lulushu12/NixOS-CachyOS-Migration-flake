"""Payload types stored on `Tree` node `.data`.

Each Textual tree node carries one of these small dataclasses so the app
can figure out, from `tree.cursor_node.data` alone, what a highlighted row
represents and which core-library call applies to it.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.model import ImportEntry, PackageEntry, PackageList
from ..core.model import TreeNode as CoreTreeNode


@dataclass
class BranchData:
    """The top-level "System" / "Home" branch nodes."""

    kind: str  # 'system' | 'home'


@dataclass
class ModuleData:
    """A module file node (a root, or resolved from an enabled import)."""

    tree_node: CoreTreeNode
    # The import that brought this module in, and the TreeNode that owns
    # that import's `imports` block. None for the tree roots.
    import_entry: ImportEntry | None = None
    import_parent: CoreTreeNode | None = None


@dataclass
class PlistData:
    tree_node: CoreTreeNode
    plist: PackageList


@dataclass
class SectionData:
    tree_node: CoreTreeNode
    plist: PackageList
    title: str


@dataclass
class PackageData:
    tree_node: CoreTreeNode
    plist: PackageList
    entry: PackageEntry


@dataclass
class ImportLeafData:
    """A disabled / missing / cyclic import: shown, but not descended into."""

    parent: CoreTreeNode
    entry: ImportEntry
