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


async def wait_until(pilot, predicate, timeout: float = 3.0) -> None:
    """Pump the event loop until `predicate()` is true, instead of guessing
    a fixed number of pauses — robust against worker-thread scheduling
    jitter (e.g. actions that hop to a thread and back via call_from_thread)."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while not predicate():
        if loop.time() >= deadline:
            raise AssertionError(f"condition not met within {timeout}s")
        await pilot.pause()
        await asyncio.sleep(0.02)


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
            await wait_until(pilot, lambda: len(app.screen_stack) == 1)

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
            await wait_until(pilot, lambda: len(app.screen_stack) == 1)

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


# ── 7. hotkeys: find, vim keys, yank, comment, undo, validate, help ──────────

def test_find_overlay_jumps_and_cycles(tmp_config: Path):
    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)

            await pilot.press("slash")
            await pilot.pause()
            find = app.query_one("#find-input")
            assert find.display and find.has_focus

            await pilot.press(*"lutris")
            await pilot.pause()
            node = tree.cursor_node
            assert isinstance(node.data, PackageData)
            assert node.data.entry.name == "lutris"

            # Esc closes and returns focus to the tree, cursor stays put.
            await pilot.press("escape")
            await pilot.pause()
            assert not find.display
            assert tree.has_focus
            assert tree.cursor_node is node

            # Typing action keys inside find must not trigger actions:
            # "add" contains 'a' and 'd' — no dialog may open.
            await pilot.press("slash")
            await pilot.press(*"add")
            await pilot.pause()
            assert len(app.screen_stack) == 1
            await pilot.press("escape")

    run(scenario())


def test_vim_navigation_keys(tmp_config: Path):
    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)
            tree.focus()
            await pilot.pause()

            await pilot.press("g")
            assert tree.cursor_line == 0
            await pilot.press("j")
            assert tree.cursor_line == 1
            await pilot.press("k")
            assert tree.cursor_line == 0
            await pilot.press("G")
            assert tree.cursor_line == tree.last_line

            gaming = find_module(tree, "gaming.nix")
            tree.select_node(gaming)
            await pilot.pause()
            await pilot.press("h")
            assert not gaming.is_expanded
            await pilot.press("l")
            assert gaming.is_expanded

    run(scenario())


def test_yank_and_help_and_validate(tmp_config: Path):
    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)
            lutris = find_package(find_module(tree, "gaming.nix"), "lutris")
            tree.select_node(lutris)
            await pilot.pause()

            await pilot.press("y")
            assert any("Copied: lutris" in n.message for n in notifications(app))

            await pilot.press("question_mark")
            await pilot.pause()
            assert len(app.screen_stack) == 2
            await pilot.press("escape")
            await pilot.pause()
            assert len(app.screen_stack) == 1

            # No nix in this container → warning, not a crash.
            await pilot.press("v")
            assert any("nix not found" in n.message for n in notifications(app))

    run(scenario())


def test_edit_comment_hotkey(tmp_config: Path):
    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)
            lutris = find_package(find_module(tree, "gaming.nix"), "lutris")
            tree.select_node(lutris)
            await pilot.pause()

            await pilot.press("c")
            await pilot.pause()
            comment_input = app.screen.query_one("#comment-value", Input)
            comment_input.value = "my launcher of choice"
            await pilot.click("#save")
            await pilot.pause()

            await pilot.click("#apply-btn")
            await wait_until(pilot, lambda: len(app.screen_stack) == 1)

            text = (tmp_config / "modules/gaming.nix").read_text()
            assert "lutris" in text and "my launcher of choice" in text

    run(scenario())


def test_undo_hotkey_reverts(tmp_config: Path):
    import subprocess

    for cmd in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "t@t"],
        ["git", "config", "user.name", "t"],
        ["git", "add", "-A"],
        ["git", "commit", "-qm", "init"],
    ):
        subprocess.run(cmd, cwd=tmp_config, check=True)

    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=True)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)
            original = (tmp_config / "modules/gaming.nix").read_text()

            lutris = find_package(find_module(tree, "gaming.nix"), "lutris")
            tree.select_node(lutris)
            await pilot.pause()
            await pilot.press("space")
            await pilot.pause()
            await pilot.click("#apply-btn")
            await wait_until(pilot, lambda: len(app.screen_stack) == 1)
            assert "# lutris" in (tmp_config / "modules/gaming.nix").read_text()

            # "u" looks up the last commit in a worker thread before the
            # confirm screen appears — wait for the screen, not a pause count.
            await pilot.press("u")
            await wait_until(pilot, lambda: len(app.screen_stack) == 2)
            await pilot.click("#yes")
            await wait_until(
                pilot,
                lambda: (tmp_config / "modules/gaming.nix").read_text() == original,
            )

    run(scenario())


# ── 8. regression: bracketed content must not crash markup rendering ────────

def test_detail_panel_handles_bracket_content(tmp_config: Path):
    """hardware-configuration.nix has option values like
    `[ "fmask=0077" "dmask=0077" ]` — Static() defaults to parsing its
    content as Rich markup, and '[...]' reads as a markup tag there,
    raising MarkupError. The detail panel must render this as plain text.
    """
    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)
            hwconf = find_module(tree, "hardware-configuration.nix")
            assert hwconf is not None
            tree.select_node(hwconf)
            await pilot.pause()  # would raise MarkupError before the fix

            detail = app.query_one("#detail")
            content = detail._Static__content
            assert "fmask=0077" in content

    run(scenario())


def test_search_results_with_brackets_do_not_crash(tmp_config: Path, monkeypatch):
    """nixpkgs descriptions routinely contain '[' / ']'; DataTable.add_row
    also markup-parses plain str cells by default."""
    from nixcfg.core.search import SearchResult

    monkeypatch.setattr("nixcfg.core.search.available", lambda: True)
    monkeypatch.setattr(
        "nixcfg.core.search.search_nixpkgs",
        lambda *a, **k: [
            SearchResult(attr="foo", version="1.0", description="A tool for [testing]")
        ],
    )

    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            tree = app.query_one("#nav-tree", Tree)
            apps_node = find_module(tree, "home/modules/apps.nix")
            tree.select_node(apps_node)
            await pilot.pause()

            await pilot.press("a")
            await pilot.pause()
            query_input = app.screen.query_one("#pick-query", Input)
            query_input.value = "foo"
            from textual.widgets import DataTable

            await pilot.click("#search-btn")
            # would raise MarkupError before the fix, surfaced as a worker
            # exception rather than a normal predicate timeout
            await wait_until(
                pilot,
                lambda: app.screen.query_one("#pick-results", DataTable).row_count
                == 1,
            )

    run(scenario())


def test_notify_with_bracket_content_does_not_crash(tmp_config: Path):
    """Notifications carry nix stderr / paths / package names; App.notify
    defaults to markup=True upstream, so '[ "fmask=0077" ]' raised
    MarkupError. NixcfgApp.notify must default to plain text."""
    async def scenario():
        app = NixcfgApp(root=tmp_config, validate=False, commit=False)
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause()
            app.notify('nix error: expected [ "fmask=0077" ] here', severity="error")
            await pilot.pause()  # rendering the toast would raise before the fix
            assert any("fmask" in n.message for n in notifications(app))

    run(scenario())
