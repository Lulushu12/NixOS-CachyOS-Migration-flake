"""Section-aware parser for Nix module files.

This is deliberately NOT a full Nix parser. The config this tool manages
follows a consistent house style (see the repo's modules/), and the parser
targets exactly that:

  * `imports = [ … ];` blocks with one `./path.nix` per line, optionally
    followed by an aligned `# comment`; commented-out entries are treated
    as disabled imports.
  * `<attrpath> = with pkgs; [ … ];` package lists with one package per
    line, `# ── Title ──…` section headers, aligned inline comments,
    commented-out entries as disabled packages, and parenthesized
    expressions (possibly spanning lines) as opaque entries.
  * Scalar option assignments (`programs.steam.enable = true;`), tracked
    through nested attrset blocks (`hardware.nvidia = { … };`) so the full
    attribute path is reconstructed. Best-effort, for display.

Anything the parser does not recognize is left untouched by the editor,
so unrecognized syntax can never be corrupted — only ignored.
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import (
    ImportEntry,
    ImportsBlock,
    ModuleFile,
    OptionEntry,
    PackageEntry,
    PackageList,
    SectionInfo,
)

# `# ── Title ──────…` — box-drawing dashes on both sides, title optional.
SECTION_RE = re.compile(r"^\s*#\s*[─]{2,}\s*(?P<title>.*?)\s*[─]*\s*$")

# A package attribute path: `mangohud`, `kdePackages.kdenlive`, `nvtopPackages.nvidia`.
ATTR_RE = re.compile(r"^[A-Za-z_][\w'+-]*(\.[A-Za-z_][\w'+-]*)*$")

# An active package line: attr path + optional inline comment.
PKG_LINE_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z_][\w'+.-]*)\s*(?:#[ \t]?(?P<comment>.*))?$"
)

# A disabled package line: `# davinci-resolve  # why it is disabled`.
# The name must start lowercase so prose comments ("These are…") don't match,
# and any text after the name must itself be a comment.
DISABLED_PKG_RE = re.compile(
    r"^\s*#\s*(?P<name>[a-z_][\w'+.-]*)\s*(?:#[ \t]?(?P<comment>.*))?$"
)

# Import path entries, active and disabled.
IMPORT_LINE_RE = re.compile(
    r"^\s*(?P<path>\.{0,2}/[\w./ -]*?\.nix)\s*(?:#[ \t]?(?P<comment>.*))?$"
)
DISABLED_IMPORT_RE = re.compile(
    r"^\s*#\s*(?P<path>\.{0,2}/[\w./ -]*?\.nix)\s*(?:#[ \t]?(?P<comment>.*))?$"
)

# `attrpath = ` openers.
LIST_OPEN_RE = re.compile(
    r"^\s*(?P<attr>[\w.'-]+)\s*=\s*(?P<withpkgs>with\s+pkgs\s*;\s*)?\[(?P<rest>.*)$"
)
ATTRSET_OPEN_RE = re.compile(r"^\s*(?P<attr>[\w.'-]+)\s*=\s*(?:rec\s+)?\{\s*(?:#.*)?$")
OPTION_RE = re.compile(
    r"^\s*(?P<attr>[\w.'-]+)\s*=\s*(?P<value>[^;]+);\s*(?:#.*)?$"
)
BLOCK_CLOSE_RE = re.compile(r"^\s*\};?\s*(?:#.*)?$")

SIMPLE_VALUE_RE = re.compile(r'^(true|false|-?\d+|"[^"]*")$')


def strip_comment(line: str) -> str:
    """Best-effort removal of a trailing comment (no string-awareness needed
    for bracket counting in this house style)."""
    idx = line.find("#")
    return line if idx == -1 else line[:idx]


def _leading_comment_block(lines: list[str]) -> str:
    out: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith("#"):
            out.append(s.lstrip("#").strip())
        elif s == "":
            if out:
                break
        else:
            break
    # First non-decoration line is the best one-line description.
    return "\n".join(out)


def _parse_imports_block(lines: list[str], start: int, end: int) -> ImportsBlock:
    block = ImportsBlock(start_line=start, end_line=end)
    for i in range(start + 1, end):
        line = lines[i]
        m = IMPORT_LINE_RE.match(line)
        if m:
            raw = m.group("path").strip()
            block.entries.append(
                ImportEntry(
                    raw=raw,
                    resolved=None,
                    comment=(m.group("comment") or "").strip() or None,
                    enabled=True,
                    line=i,
                )
            )
            continue
        m = DISABLED_IMPORT_RE.match(line)
        if m:
            block.entries.append(
                ImportEntry(
                    raw=m.group("path").strip(),
                    resolved=None,
                    comment=(m.group("comment") or "").strip() or None,
                    enabled=False,
                    line=i,
                )
            )
    return block


def _parse_package_list(
    lines: list[str], attr: str, with_pkgs: bool, start: int, end: int
) -> PackageList:
    plist = PackageList(
        attrpath=attr,
        start_line=start,
        end_line=end,
        with_pkgs=with_pkgs,
    )
    section: str | None = None
    i = start + 1
    while i < end:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        m = SECTION_RE.match(line)
        if m:
            title = m.group("title").strip()
            if title:
                section = title
                plist.sections.append(SectionInfo(title=title, line=i))
            i += 1
            continue

        # Parenthesized expression, possibly spanning multiple lines.
        if stripped.startswith("("):
            depth = 0
            j = i
            expr_lines: list[str] = []
            comment: str | None = None
            while j < end:
                code = lines[j]
                depth += code.count("(") - code.count(")")
                expr_lines.append(lines[j].strip())
                if depth <= 0:
                    # Inline comment after the closing paren.
                    tail = lines[j]
                    close = tail.rfind(")")
                    hash_idx = tail.find("#", close)
                    if hash_idx != -1:
                        comment = tail[hash_idx + 1 :].strip()
                        expr_lines[-1] = tail[:hash_idx].strip()
                    break
                j += 1
            plist.packages.append(
                PackageEntry(
                    name="\n".join(expr_lines),
                    comment=comment,
                    enabled=True,
                    line=i,
                    end_line=j,
                    is_expr=True,
                    section=section,
                )
            )
            i = j + 1
            continue

        if stripped.startswith("#"):
            m = DISABLED_PKG_RE.match(line)
            # `rest must be a comment or empty` is enforced by the regex; a
            # prose line like `# These are widgets…` fails the full match.
            if m:
                plist.packages.append(
                    PackageEntry(
                        name=m.group("name"),
                        comment=(m.group("comment") or "").strip() or None,
                        enabled=False,
                        line=i,
                        end_line=i,
                        is_expr=False,
                        section=section,
                    )
                )
            i += 1
            continue

        m = PKG_LINE_RE.match(line)
        if m and ATTR_RE.match(m.group("name")):
            plist.packages.append(
                PackageEntry(
                    name=m.group("name"),
                    comment=(m.group("comment") or "").strip() or None,
                    enabled=True,
                    line=i,
                    end_line=i,
                    is_expr=False,
                    section=section,
                )
            )
        i += 1
    return plist


def _find_list_end(lines: list[str], start: int) -> int:
    """Return the index of the line closing a `[` opened on `start`."""
    depth = 0
    for i in range(start, len(lines)):
        code = strip_comment(lines[i])
        depth += code.count("[") - code.count("]")
        if depth <= 0 and i > start:
            return i
        if depth <= 0 and i == start and "]" in code:
            return i  # single-line list
    return len(lines) - 1


READ_ONLY_MARKERS = ("do not edit", "do not modify", "auto-generated", "autogenerated")


def parse_module(path: Path, root: Path) -> ModuleFile:
    text = path.read_text()
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # keep `lines` newline-free; ModuleFile.text re-adds the final \n

    header = _leading_comment_block(lines)
    imports_block: ImportsBlock | None = None
    package_lists: list[PackageList] = []
    options: list[OptionEntry] = []

    # Attrset nesting stack for option path reconstruction.
    stack: list[str] = []
    in_multiline_string = False

    i = 0
    while i < len(lines):
        line = lines[i]

        if "''" in line:
            if line.count("''") % 2 == 1:
                in_multiline_string = not in_multiline_string
            i += 1
            continue
        if in_multiline_string:
            i += 1
            continue
        if line.strip().startswith("#"):
            i += 1
            continue

        m = LIST_OPEN_RE.match(line)
        if m:
            attr = m.group("attr")
            end = _find_list_end(lines, i)
            full_attr = ".".join(stack + [attr])
            if attr == "imports":
                imports_block = _parse_imports_block(lines, i, end)
            elif m.group("withpkgs"):
                package_lists.append(
                    _parse_package_list(lines, full_attr, True, i, end)
                )
            elif end == i:
                # Single-line list value — record as a display-only option.
                value = strip_comment(line.split("=", 1)[1]).strip().rstrip(";")
                options.append(
                    OptionEntry(attrpath=full_attr, value=value, line=i, simple=False)
                )
            i = end + 1
            continue

        m = ATTRSET_OPEN_RE.match(line)
        if m:
            stack.append(m.group("attr"))
            i += 1
            continue

        if BLOCK_CLOSE_RE.match(line):
            if stack:
                stack.pop()
            i += 1
            continue

        m = OPTION_RE.match(line)
        if m:
            attr = m.group("attr")
            value = m.group("value").strip()
            full_attr = ".".join(stack + [attr])
            options.append(
                OptionEntry(
                    attrpath=full_attr,
                    value=value,
                    line=i,
                    simple=bool(SIMPLE_VALUE_RE.match(value)),
                )
            )
        i += 1

    # Only the header's FIRST line may mark a file read-only — later lines
    # often describe *other* files ("hardware-configuration.nix … is
    # auto-generated") and must not poison this one.
    first_header_line = header.split("\n", 1)[0].lower()
    read_only = path.name == "hardware-configuration.nix" or any(
        marker in first_header_line for marker in READ_ONLY_MARKERS
    )

    try:
        rel = str(path.relative_to(root))
    except ValueError:
        rel = str(path)

    module = ModuleFile(
        path=path,
        rel=rel,
        lines=lines,
        header_comment=header,
        imports_block=imports_block,
        package_lists=package_lists,
        options=options,
        read_only=read_only,
    )

    # Resolve import paths relative to the module's own directory.
    if module.imports_block:
        for entry in module.imports_block.entries:
            candidate = (path.parent / entry.raw).resolve()
            if candidate.exists():
                entry.resolved = candidate
    return module
