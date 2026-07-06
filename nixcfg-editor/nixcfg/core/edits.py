"""Edit operations.

Every operation is pure: it takes parsed model objects, computes new file
contents, and returns an EditPlan describing before/after text per file.
Nothing touches disk here — `pipeline.apply()` does that, with validation
and git safety around it. After a successful apply the tree must be
re-loaded, since all recorded line numbers are stale.

Formatting rules mirror the config's house style:
  * entries are indented to match their neighbors,
  * inline comments are aligned to the section's existing comment column,
  * new sections get a `# ── Title ──…` header padded like existing ones.
"""

from __future__ import annotations

import difflib
import os
from dataclasses import dataclass, field
from pathlib import Path

from .model import ImportEntry, ModuleFile, PackageEntry, PackageList

HEADER_WIDTH = 78  # target end column for `# ── Title ──…` headers


class EditError(Exception):
    pass


@dataclass
class FileEdit:
    path: Path
    before: str  # empty string for newly created files
    after: str
    create: bool = False

    def diff(self) -> str:
        rel = self.path.name if self.create else str(self.path)
        return "".join(
            difflib.unified_diff(
                self.before.splitlines(keepends=True),
                self.after.splitlines(keepends=True),
                fromfile=f"a/{rel}" if not self.create else "/dev/null",
                tofile=f"b/{rel}",
            )
        )


@dataclass
class EditPlan:
    description: str  # used as the git commit message
    edits: list[FileEdit] = field(default_factory=list)

    def diff(self) -> str:
        return "\n".join(e.diff() for e in self.edits)


def _guard_writable(module: ModuleFile) -> None:
    if module.read_only:
        raise EditError(f"{module.rel} is marked read-only (auto-generated)")


def _entry_indent(lines: list[str], plist: PackageList) -> str:
    for entry in plist.packages:
        line = lines[entry.line]
        return line[: len(line) - len(line.lstrip())].replace("#", " ")
    # No entries yet: indent two spaces past the list opener.
    opener = lines[plist.start_line]
    return " " * (len(opener) - len(opener.lstrip()) + 2)


def _comment_column(lines: list[str], entries: list[PackageEntry]) -> int | None:
    cols = []
    for e in entries:
        if e.is_expr or e.comment is None:
            continue
        idx = lines[e.line].find("#", 1 if not e.enabled else 0)
        if not e.enabled:
            # For disabled entries the first '#' is the disable marker.
            idx = lines[e.line].find("#", idx + 1)
        if idx > 0:
            cols.append(idx)
    return max(cols) if cols else None


def _format_entry(indent: str, name: str, comment: str | None, col: int | None) -> str:
    line = indent + name
    if comment:
        target = col if col is not None else len(line) + 2
        pad = max(target - len(line), 2)
        line += " " * pad + "# " + comment
    return line


def _section_header(indent: str, title: str) -> str:
    prefix = f"{indent}# ── {title} "
    dashes = max(HEADER_WIDTH - len(prefix), 4)
    return prefix + "─" * dashes


def _make_edit(module: ModuleFile, new_lines: list[str]) -> FileEdit:
    return FileEdit(path=module.path, before=module.text, after="\n".join(new_lines) + "\n")


def add_package(
    module: ModuleFile,
    plist: PackageList,
    name: str,
    comment: str | None = None,
    section: str | None = None,
) -> EditPlan:
    """Insert `name` into `plist`, at the end of `section` if given.

    A section title that doesn't exist yet is created as a new
    `# ── Title ──…` header at the end of the list.
    """
    _guard_writable(module)
    for entry in plist.packages:
        if not entry.is_expr and entry.name == name and entry.enabled:
            raise EditError(f"{name} is already in {plist.attrpath} ({module.rel})")

    lines = module.lines.copy()
    indent = _entry_indent(module.lines, plist)

    section_titles = [s.title for s in plist.sections]
    if section is not None and section in section_titles:
        neighbors = [p for p in plist.packages if p.section == section]
        col = _comment_column(module.lines, neighbors)
        if neighbors:
            insert_at = max(p.end_line for p in neighbors) + 1
        else:
            insert_at = next(s.line for s in plist.sections if s.title == section) + 1
        lines.insert(insert_at, _format_entry(indent, name, comment, col))
    elif section is not None:
        # New section at the end of the list.
        block = [
            "",
            _section_header(indent, section),
            _format_entry(indent, name, comment, None),
        ]
        lines[plist.end_line:plist.end_line] = block
    else:
        col = _comment_column(module.lines, plist.packages)
        if plist.packages:
            insert_at = max(p.end_line for p in plist.packages) + 1
        else:
            insert_at = plist.start_line + 1
        lines.insert(insert_at, _format_entry(indent, name, comment, col))

    where = f" under '{section}'" if section else ""
    return EditPlan(
        description=f"nixcfg: add {name} to {plist.attrpath} in {module.rel}{where}",
        edits=[_make_edit(module, lines)],
    )


def set_package_enabled(
    module: ModuleFile, entry: PackageEntry, enabled: bool
) -> EditPlan:
    """Comment out / uncomment a package entry.

    Multi-line expressions can be disabled (each line commented) but not
    re-enabled through the tool afterwards — once commented they read as
    prose. Single-name entries round-trip fine.
    """
    _guard_writable(module)
    if entry.enabled == enabled:
        raise EditError(f"{entry.display_name} is already {'enabled' if enabled else 'disabled'}")
    if entry.is_expr and enabled:
        raise EditError("Re-enabling a commented expression isn't supported; edit the file directly")

    lines = module.lines.copy()
    if enabled:
        line = lines[entry.line]
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        lines[entry.line] = indent + stripped.removeprefix("#").lstrip()
    else:
        for i in range(entry.line, entry.end_line + 1):
            line = lines[i]
            stripped = line.lstrip()
            indent = line[: len(line) - len(stripped)]
            lines[i] = indent + "# " + stripped
    verb = "enable" if enabled else "disable"
    return EditPlan(
        description=f"nixcfg: {verb} {entry.display_name} in {module.rel}",
        edits=[_make_edit(module, lines)],
    )


def remove_package(module: ModuleFile, entry: PackageEntry) -> EditPlan:
    _guard_writable(module)
    lines = module.lines.copy()
    del lines[entry.line : entry.end_line + 1]
    return EditPlan(
        description=f"nixcfg: remove {entry.display_name} from {module.rel}",
        edits=[_make_edit(module, lines)],
    )


def set_import_enabled(
    module: ModuleFile, entry: ImportEntry, enabled: bool
) -> EditPlan:
    """Comment out / uncomment an import line — disables/enables a module."""
    _guard_writable(module)
    if entry.enabled == enabled:
        raise EditError(f"{entry.raw} is already {'enabled' if enabled else 'disabled'}")
    lines = module.lines.copy()
    line = lines[entry.line]
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    if enabled:
        lines[entry.line] = indent + stripped.removeprefix("#").lstrip()
    else:
        lines[entry.line] = indent + "# " + stripped
    verb = "enable" if enabled else "disable"
    return EditPlan(
        description=f"nixcfg: {verb} import {entry.raw} in {module.rel}",
        edits=[_make_edit(module, lines)],
    )


def _import_comment_column(lines: list[str], entries: list[ImportEntry]) -> int | None:
    cols = []
    for e in entries:
        if e.comment is None:
            continue
        line = lines[e.line]
        start = 0
        if not e.enabled:
            start = line.find("#") + 1
        idx = line.find("#", start)
        if idx > 0:
            cols.append(idx)
    return max(cols) if cols else None


def add_import(
    module: ModuleFile, import_path: str, comment: str | None = None
) -> EditPlan:
    """Append an entry to the module's `imports = [ … ];` block."""
    _guard_writable(module)
    block = module.imports_block
    if block is None:
        raise EditError(f"{module.rel} has no imports block")
    for e in block.entries:
        if e.raw == import_path:
            raise EditError(f"{import_path} is already imported in {module.rel}")

    lines = module.lines.copy()
    if block.entries:
        ref = lines[block.entries[0].line]
        indent = ref[: len(ref) - len(ref.lstrip())].replace("#", " ")
        insert_at = max(e.line for e in block.entries) + 1
    else:
        opener = lines[block.start_line]
        indent = " " * (len(opener) - len(opener.lstrip()) + 2)
        insert_at = block.start_line + 1
    col = _import_comment_column(module.lines, block.entries)

    line = indent + import_path
    if comment:
        target = col if col is not None else len(line) + 4
        line += " " * max(target - len(line), 2) + "# " + comment
    lines.insert(insert_at, line)
    return EditPlan(
        description=f"nixcfg: import {import_path} in {module.rel}",
        edits=[_make_edit(module, lines)],
    )


MODULE_TEMPLATE = """\
# {description}

{{ pkgs, ... }}:

{{
  {pkg_attr} = with pkgs; [
  ];
}}
"""


def create_module(
    parent: ModuleFile,
    new_path: Path,
    description: str,
    kind: str,
    comment: str | None = None,
) -> EditPlan:
    """Scaffold a new module file and wire its import into `parent`.

    `kind` is 'system' (environment.systemPackages) or 'home' (home.packages);
    it should match the tree the parent belongs to.
    """
    if new_path.exists():
        raise EditError(f"{new_path} already exists")
    if kind not in ("system", "home"):
        raise EditError(f"unknown module kind: {kind}")

    pkg_attr = "environment.systemPackages" if kind == "system" else "home.packages"
    content = MODULE_TEMPLATE.format(description=description, pkg_attr=pkg_attr)

    rel = os.path.relpath(new_path, parent.path.parent)
    if not rel.startswith("."):
        rel = "./" + rel

    plan = add_import(parent, rel, comment or description)
    plan.description = f"nixcfg: new module {new_path.name} imported by {parent.rel}"
    plan.edits.insert(0, FileEdit(path=new_path, before="", after=content, create=True))
    return plan
