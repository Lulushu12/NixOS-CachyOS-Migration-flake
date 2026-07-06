"""Pilot-based tests for the Textual TUI frontend.

No pytest-asyncio plugin is available in this environment, so each test
wraps its `async def` body and drives it with `asyncio.run()` directly.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.widgets import Button, Input, Tree

from nixcfg.tui.app import NixcfgApp
from nixcfg.tui.treedata import BranchData, ModuleData, PackageData

SIZE = (120, 45)


def run(coro):
    return asyncio.run(coro)


def find_node(node, predicate):
    if predicate(node):
        return node
    for child in node.children:
        found = find_node(child, predicate)
        if found is not None:
            return found
    return None


def find_branch(tree: Tree, kind: str):
    return find_node(
        tree.root, lambda n: isinstance(n.data, BranchData) and n.data.kind == kind
    )


def find_module(tree: Tree, rel_suffix: str):
    return find_node(
        tree.root,
        lambda n: isinstance(n.data, ModuleData) and n.data.tree_node.file.rel.endswith(rel_suffix),
    )


def find_package(start_node, name: str):
    return find_node(
        start_node,
        lambda n: isinstance(n.data, PackageData) and n.data.entry.name == name,
    )


def notifications(app):
    return list(app._notifications)


# ── 1. launch + tree structure ───────────────────────────────────────────────

def test_app_launches_and_shows_tree(tmp_config: Path):
    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)
            assert find_branch(tree, "system") is not None
            assert find_branch(tree, "home") is not None
            gaming = find_module(tree, "gaming.nix")
            assert gaming is not None
            assert gaming.data.tree_node.file.rel == "modules/gaming.nix"

    run(scenario())


# ── 2. expand to a package leaf, detail panel updates ────────────────────────

def test_expand_to_package_leaf_updates_detail(tmp_config: Path):
    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)

            gaming = find_module(tree, "gaming.nix")
            assert gaming is not None
            tree.select_node(gaming)
            await pilot.pause()

            lutris = find_package(gaming, "lutris")
            assert lutris is not None
            tree.select_node(lutris)
            await pilot.pause()

            assert tree.cursor_node is lutris
            detail = app.query_one("#detail")
            content = detail._Static__content
            assert "lutris" in content
            assert "Launchers & managers" in content

    run(scenario())


# ── 3. add package, search unavailable → typed attribute name ───────────────

def test_add_package_search_unavailable(tmp_config: Path, monkeypatch):
    monkeypatch.setattr("nixcfg.core.search.available", lambda: False)

    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)

            apps_node = find_module(tree, "home/modules/apps.nix")
            assert apps_node is not None
            tree.select_node(apps_node)
            await pilot.pause()

            await pilot.press("a")
            await pilot.pause()

            query_input = app.screen.query_one("#pick-query", Input)
            query_input.value = "firefox"
            await pilot.click("#use-typed")
            await pilot.pause()

            # Step 2: comment/section screen.
            add_button = app.screen.query_one("#add", Button)
            await pilot.click(add_button)
            await pilot.pause()

            # Step 3: diff screen — apply.
            await pilot.click("#apply-btn")
            await pilot.pause()
            await pilot.pause()
            await pilot.pause()

            text = (tmp_config / "home/modules/apps.nix").read_text()
            assert "firefox" in text

    run(scenario())


# ── 4. toggle a package off via space, apply in diff modal ──────────────────

def test_toggle_package_disable(tmp_config: Path):
    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)

            gaming = find_module(tree, "gaming.nix")
            assert gaming is not None
            lutris = find_package(gaming, "lutris")
            assert lutris is not None
            tree.select_node(lutris)
            await pilot.pause()

            await pilot.press("space")
            await pilot.pause()

            await pilot.click("#apply-btn")
            await pilot.pause()
            await pilot.pause()
            await pilot.pause()

            text = (tmp_config / "modules/gaming.nix").read_text()
            assert "# lutris" in text

    run(scenario())


# ── 5. duplicate package → EditError surfaces as a notification ─────────────

def test_add_duplicate_package_shows_error(tmp_config: Path, monkeypatch):
    monkeypatch.setattr("nixcfg.core.search.available", lambda: False)

    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)

            apps_node = find_module(tree, "home/modules/apps.nix")
            assert apps_node is not None
            tree.select_node(apps_node)
            await pilot.pause()

            before_text = (tmp_config / "home/modules/apps.nix").read_text()

            await pilot.press("a")
            await pilot.pause()

            query_input = app.screen.query_one("#pick-query", Input)
            query_input.value = "brave"  # already present under "Browsers"
            await pilot.click("#use-typed")
            await pilot.pause()

            await pilot.click("#add")
            await pilot.pause()

            notes = notifications(app)
            assert any(n.severity == "error" and "already" in n.message for n in notes)

            after_text = (tmp_config / "home/modules/apps.nix").read_text()
            assert before_text == after_text
            # No diff screen should have been pushed.
            assert len(app.screen_stack) == 1

    run(scenario())


# ── 6. keyboard: arrows fold/unfold tree nodes, Esc closes dialogs ───────────

def test_arrow_keys_collapse_and_expand(tmp_config: Path):
    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)
            gaming = find_module(tree, "gaming.nix")
            tree.select_node(gaming)
            await pilot.pause()

            assert gaming.is_expanded
            await pilot.press("left")
            assert not gaming.is_expanded
            await pilot.press("right")
            assert gaming.is_expanded

            # Left on a leaf jumps to its parent.
            lutris = find_package(gaming, "lutris")
            tree.select_node(lutris)
            await pilot.pause()
            await pilot.press("left")
            assert tree.cursor_node is lutris.parent

    run(scenario())


def test_escape_closes_dialogs_without_changes(tmp_config: Path, monkeypatch):
    monkeypatch.setattr("nixcfg.core.search.available", lambda: False)

    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)
            before = (tmp_config / "modules/gaming.nix").read_text()

            gaming = find_module(tree, "gaming.nix")
            lutris = find_package(gaming, "lutris")
            tree.select_node(lutris)
            await pilot.pause()

            # Esc out of the pick-package dialog.
            await pilot.press("a")
            await pilot.pause()
            assert len(app.screen_stack) == 2
            await pilot.press("escape")
            await pilot.pause()
            assert len(app.screen_stack) == 1

            # Esc out of the diff dialog after a toggle — nothing written.
            await pilot.press("space")
            await pilot.pause()
            assert len(app.screen_stack) == 2
            await pilot.press("escape")
            await pilot.pause()
            assert len(app.screen_stack) == 1
            assert (tmp_config / "modules/gaming.nix").read_text() == before

    run(scenario())
