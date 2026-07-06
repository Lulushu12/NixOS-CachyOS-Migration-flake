"""Textual TUI application: browse and edit a modular NixOS flake config."""

from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Header, Static, Tree
from textual.widgets.tree import TreeNode as WidgetTreeNode

from ..core import edits, search
from ..core.edits import EditError
from ..core.graph import ConfigError, load_tree
from ..core.model import ConfigTree
from ..core.model import TreeNode as CoreTreeNode
from ..core.pipeline import ApplyResult, Pipeline
from .dialogs import (
    ConfirmScreen,
    DiffScreen,
    NewModuleScreen,
    PackageDetailsScreen,
    PickPackageScreen,
)
from .treedata import (
    BranchData,
    ImportLeafData,
    ModuleData,
    PackageData,
    PlistData,
    SectionData,
)

MAX_DESCRIPTION_LEN = 60


def _truncate(text: str, limit: int = MAX_DESCRIPTION_LEN) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _module_label(node: CoreTreeNode) -> Text:
    label = Text(node.file.rel)
    if node.file.read_only:
        label.append(" \U0001f512")  # lock
    return label


def _package_label(entry) -> Text:
    label = Text(entry.display_name)
    if not entry.enabled:
        label.stylize("dim strike")
    if entry.comment:
        suffix = f"  # {entry.comment}"
        if len(label.plain) + len(suffix) <= 80:
            label.append(suffix, style="dim")
    return label


def _import_leaf_label(entry) -> Text:
    if not entry.enabled:
        label = Text(f"{entry.raw} (disabled)", style="dim red")
    elif entry.resolved is None:
        label = Text(f"{entry.raw} (missing)", style="dim yellow")
    else:
        label = Text(f"{entry.raw} (cycle)", style="dim yellow")
    return label


class NavTree(Tree):
    """Tree with file-manager keyboard conventions.

    Space is handed to the app (enable/disable) instead of Textual's default
    expand/collapse; since `auto_expand` is off, right/left take over
    folding: right expands the highlighted node, left collapses it (or jumps
    to the parent when there is nothing to collapse).
    """

    BINDINGS = [
        Binding("right", "expand_current", "Expand", show=False),
        Binding("left", "collapse_current", "Collapse", show=False),
    ]

    def action_toggle_node(self) -> None:
        self.app.action_toggle_enabled()

    def action_expand_current(self) -> None:
        node = self.cursor_node
        if node is not None and node.allow_expand:
            node.expand()

    def action_collapse_current(self) -> None:
        node = self.cursor_node
        if node is None:
            return
        if node.allow_expand and node.is_expanded:
            node.collapse()
        else:
            self.action_cursor_parent()


class NixcfgApp(App):
    """Browser / editor for a modular NixOS flake config."""

    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "reload", "Reload"),
        Binding("a", "add_package", "Add pkg"),
        Binding("space", "toggle_enabled", "Toggle enable"),
        Binding("d", "remove_package", "Remove pkg"),
        Binding("n", "new_module", "New module"),
    ]

    def __init__(self, root: Path, validate: bool = True, commit: bool = True) -> None:
        super().__init__()
        self._root_arg = root
        self.validate = validate
        self.commit = commit
        self.tree_data: ConfigTree | None = None
        self._path_index: dict[Path, WidgetTreeNode] = {}
        self._last_plan = None

    # ── layout ────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            yield NavTree("nixcfg", id="nav-tree")
            with VerticalScroll(id="detail-panel"):
                yield Static(
                    "Select a node in the tree to see details.", id="detail"
                )
        yield Footer()

    def on_mount(self) -> None:
        self.title = "nixcfg"
        tree = self.query_one("#nav-tree", NavTree)
        tree.show_root = False
        # Tree's default `auto_expand` toggles a node's expanded state on
        # every NodeSelected message — including the ones we post ourselves
        # from `select_node()` when revealing a node after an edit. Since we
        # manage expansion explicitly (everything starts expanded), turn
        # that off so selecting an already-expanded node can't collapse it.
        tree.auto_expand = False
        self.load_config()

    # ── config loading / tree building ───────────────────────────────────

    def load_config(self) -> None:
        root = self.tree_data.root if self.tree_data is not None else self._root_arg
        try:
            self.tree_data = load_tree(root)
        except ConfigError as exc:
            self.notify(str(exc), severity="error")
            return
        self.sub_title = str(self.tree_data.root)
        self.populate_tree()

    def populate_tree(self) -> None:
        tree = self.query_one("#nav-tree", NavTree)
        tree.reset("nixcfg")
        self._path_index = {}
        assert self.tree_data is not None

        sys_branch = tree.root.add("⚙ System", data=BranchData("system"))
        for root_node in self.tree_data.system_roots:
            self._add_module_node(sys_branch, root_node, None, None)

        home_branch = tree.root.add("\U0001f3e0 Home", data=BranchData("home"))
        for root_node in self.tree_data.home_roots:
            self._add_module_node(home_branch, root_node, None, None)

        tree.root.expand()
        sys_branch.expand()
        home_branch.expand()

    def _add_module_node(
        self,
        parent_widget_node: WidgetTreeNode,
        node: CoreTreeNode,
        import_entry,
        import_parent: CoreTreeNode | None,
    ) -> WidgetTreeNode:
        widget_node = parent_widget_node.add(
            _module_label(node),
            data=ModuleData(
                tree_node=node, import_entry=import_entry, import_parent=import_parent
            ),
        )
        self._path_index[node.file.path] = widget_node

        for plist in node.file.package_lists:
            self._add_plist_node(widget_node, node, plist)

        for entry, child in node.children:
            if child is not None:
                self._add_module_node(widget_node, child, entry, node)
            else:
                widget_node.add_leaf(
                    _import_leaf_label(entry), data=ImportLeafData(parent=node, entry=entry)
                )

        widget_node.expand()
        return widget_node

    def _add_plist_node(
        self, parent_widget_node: WidgetTreeNode, node: CoreTreeNode, plist
    ) -> None:
        plist_widget_node = parent_widget_node.add(
            plist.attrpath, data=PlistData(tree_node=node, plist=plist)
        )
        section_nodes: dict[str, WidgetTreeNode] = {}
        for section in plist.sections:
            section_nodes[section.title] = plist_widget_node.add(
                section.title,
                data=SectionData(tree_node=node, plist=plist, title=section.title),
            )
        for entry in plist.packages:
            target = (
                section_nodes[entry.section]
                if entry.section is not None and entry.section in section_nodes
                else plist_widget_node
            )
            target.add_leaf(
                _package_label(entry),
                data=PackageData(tree_node=node, plist=plist, entry=entry),
            )
        plist_widget_node.expand()
        for sect_node in section_nodes.values():
            sect_node.expand()

    # ── detail panel ──────────────────────────────────────────────────────

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        self._update_detail(event.node.data)

    def _update_detail(self, data) -> None:
        detail = self.query_one("#detail", Static)
        detail.update(self._render_detail(data))

    def _render_detail(self, data) -> str:
        if isinstance(data, ModuleData):
            f = data.tree_node.file
            lines = [
                f"Module: {f.rel}",
                f"Kind: {data.tree_node.kind}",
                f"Read-only: {f.read_only}",
                "",
                "Header:",
                f.header_comment or "(none)",
                "",
                f"Packages: {sum(len(pl.packages) for pl in f.package_lists)}"
                f"    Options: {len(f.options)}",
            ]
            if f.options:
                lines.append("")
                lines.append("Options:")
                for opt in f.options:
                    lines.append(f"  {opt.attrpath} = {opt.value}")
            return "\n".join(lines)

        if isinstance(data, PlistData):
            pl = data.plist
            titles = ", ".join(s.title for s in pl.sections) or "(none)"
            return "\n".join(
                [
                    f"Package list: {pl.attrpath}",
                    f"with pkgs: {pl.with_pkgs}",
                    f"Packages: {len(pl.packages)}",
                    f"Sections: {titles}",
                ]
            )

        if isinstance(data, SectionData):
            count = sum(1 for p in data.plist.packages if p.section == data.title)
            return "\n".join(
                [
                    f"Section: {data.title}",
                    f"List: {data.plist.attrpath}",
                    f"Packages: {count}",
                ]
            )

        if isinstance(data, PackageData):
            e = data.entry
            return "\n".join(
                [
                    f"Package: {e.display_name}",
                    f"List: {data.plist.attrpath}",
                    f"Section: {e.section or '(none)'}",
                    f"Enabled: {e.enabled}",
                    f"Comment: {e.comment or '(none)'}",
                ]
            )

        if isinstance(data, ImportLeafData):
            e = data.entry
            return "\n".join(
                [
                    f"Import: {e.raw}",
                    f"Resolved: {e.resolved if e.resolved else '(missing)'}",
                    f"Enabled: {e.enabled}",
                    f"Comment: {e.comment or '(none)'}",
                ]
            )

        if isinstance(data, BranchData):
            return f"{data.kind.title()} modules"

        return "Select a node in the tree to see details."

    # ── helpers ───────────────────────────────────────────────────────────

    def _pipeline(self) -> Pipeline:
        assert self.tree_data is not None
        return Pipeline(self.tree_data.root, validate=self.validate, commit=self.commit)

    def _cursor_data(self):
        tree = self.query_one("#nav-tree", NavTree)
        node = tree.cursor_node
        return node.data if node is not None else None

    def _run_plan(self, plan) -> None:
        self._last_plan = plan
        self.push_screen(DiffScreen(self._pipeline(), plan), self._on_diff_result)

    def _on_diff_result(self, result: ApplyResult | None) -> None:
        if result is None:
            return  # cancelled
        if result.ok:
            self.notify(result.message, severity="information")
        else:
            message = result.message
            if result.output:
                message += f": {result.output}"
            self.notify(message, severity="error")

        edited_path = None
        if self._last_plan is not None and self._last_plan.edits:
            edited_path = self._last_plan.edits[0].path
        self.load_config()
        self._reveal_path(edited_path)

    def _reveal_path(self, path: Path | None) -> None:
        if path is None:
            return
        widget_node = self._path_index.get(path)
        if widget_node is None:
            return
        node = widget_node
        while node is not None:
            node.expand()
            node = node.parent
        tree = self.query_one("#nav-tree", NavTree)
        tree.select_node(widget_node)

    def _entry_module_file(self, kind: str):
        assert self.tree_data is not None
        roots = self.tree_data.system_roots if kind == "system" else self.tree_data.home_roots
        return roots[0].file if roots else None

    # ── actions ───────────────────────────────────────────────────────────

    def action_reload(self) -> None:
        self.load_config()
        self.notify("Reloaded from disk")

    def action_add_package(self) -> None:
        data = self._cursor_data()
        target = None
        if isinstance(data, ModuleData):
            primary = data.tree_node.file.primary_package_lists()
            if primary:
                target = (data.tree_node.file, primary[0], None)
        elif isinstance(data, PlistData):
            target = (data.tree_node.file, data.plist, None)
        elif isinstance(data, SectionData):
            target = (data.tree_node.file, data.plist, data.title)
        elif isinstance(data, PackageData):
            target = (data.tree_node.file, data.plist, data.entry.section)

        if target is None:
            self.notify(
                "Select a module, package list, section or package to add to",
                severity="warning",
            )
            return

        module_file, plist, default_section = target
        assert self.tree_data is not None

        def on_picked(picked):
            if picked is None:
                return
            attr, description = picked
            prefill = _truncate(description) if description else ""
            section_titles = [s.title for s in plist.sections]
            self.push_screen(
                PackageDetailsScreen(attr, prefill, section_titles, default_section),
                lambda res: self._on_package_details(res, module_file, plist, attr),
            )

        self.push_screen(
            PickPackageScreen(search.available(), self.tree_data.root), on_picked
        )

    def _on_package_details(self, res, module_file, plist, attr: str) -> None:
        if res is None:
            return
        comment, section = res
        try:
            plan = edits.add_package(module_file, plist, attr, comment=comment, section=section)
        except EditError as exc:
            self.notify(str(exc), severity="error")
            return
        self._run_plan(plan)

    def action_toggle_enabled(self) -> None:
        data = self._cursor_data()
        try:
            if isinstance(data, PackageData):
                plan = edits.set_package_enabled(
                    data.tree_node.file, data.entry, not data.entry.enabled
                )
            elif isinstance(data, ImportLeafData):
                plan = edits.set_import_enabled(
                    data.parent.file, data.entry, not data.entry.enabled
                )
            elif isinstance(data, ModuleData) and data.import_entry is not None:
                assert data.import_parent is not None
                plan = edits.set_import_enabled(
                    data.import_parent.file,
                    data.import_entry,
                    not data.import_entry.enabled,
                )
            else:
                self.notify("Nothing to toggle here", severity="warning")
                return
        except EditError as exc:
            self.notify(str(exc), severity="error")
            return
        self._run_plan(plan)

    def action_remove_package(self) -> None:
        data = self._cursor_data()
        if not isinstance(data, PackageData):
            self.notify("Select a package to remove", severity="warning")
            return

        def on_confirm(confirmed: bool | None) -> None:
            if not confirmed:
                return
            try:
                plan = edits.remove_package(data.tree_node.file, data.entry)
            except EditError as exc:
                self.notify(str(exc), severity="error")
                return
            self._run_plan(plan)

        self.push_screen(
            ConfirmScreen(f"Remove {data.entry.display_name}?"), on_confirm
        )

    def action_new_module(self) -> None:
        data = self._cursor_data()
        kind: str | None = None
        highlighted_module = None
        if isinstance(data, BranchData):
            kind = data.kind
        elif isinstance(data, ModuleData):
            kind = data.tree_node.kind
            highlighted_module = data.tree_node.file
        else:
            self.notify("Select a module or the System/Home branch", severity="warning")
            return

        if highlighted_module is not None and highlighted_module.imports_block is not None:
            parent_file = highlighted_module
        else:
            parent_file = self._entry_module_file(kind)
            if parent_file is None:
                self.notify(f"No {kind} root module found", severity="error")
                return

        default_dir = "modules" if kind == "system" else "home/modules"

        def on_result(res) -> None:
            if res is None:
                return
            filename, description = res
            assert self.tree_data is not None
            new_path = (self.tree_data.root / filename).resolve()
            if not new_path.is_relative_to(self.tree_data.root):
                self.notify(
                    f"{filename} is outside the config root", severity="error"
                )
                return
            try:
                plan = edits.create_module(parent_file, new_path, description, kind)
            except EditError as exc:
                self.notify(str(exc), severity="error")
                return
            self._run_plan(plan)

        self.push_screen(NewModuleScreen(default_dir), on_result)
