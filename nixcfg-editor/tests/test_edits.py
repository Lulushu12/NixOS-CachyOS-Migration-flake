from pathlib import Path

import pytest

from nixcfg.core import edits
from nixcfg.core.edits import EditError
from nixcfg.core.graph import load_tree
from nixcfg.core.parser import parse_module
from nixcfg.core.pipeline import Pipeline


def apply_plan(plan, root):
    """Apply without nix/git side effects and return re-parse helper."""
    result = Pipeline(root, validate=False, commit=False).apply(plan)
    assert result.ok, result.message
    return result


def get_module(root, rel):
    return parse_module(root / rel, root)


def get_plist(mod):
    (plist,) = mod.primary_package_lists()
    return plist


# ── add_package ──────────────────────────────────────────────────────────────

def test_add_package_into_existing_section(tmp_config):
    mod = get_module(tmp_config, "home/modules/apps.nix")
    plan = edits.add_package(
        mod, get_plist(mod), "firefox", comment="Mozilla Firefox", section="Browsers"
    )
    apply_plan(plan, tmp_config)

    mod2 = get_module(tmp_config, "home/modules/apps.nix")
    firefox = next(p for p in get_plist(mod2).packages if p.name == "firefox")
    assert firefox.section == "Browsers"
    assert firefox.comment == "Mozilla Firefox"

    # Inserted right after the last browser, comment aligned with neighbors.
    line = mod2.lines[firefox.line]
    prev = mod2.lines[firefox.line - 1]
    assert prev.strip().startswith("mullvad-browser")
    assert line.startswith("    firefox")


def test_add_package_new_section(tmp_config):
    mod = get_module(tmp_config, "home/modules/apps.nix")
    plan = edits.add_package(
        mod, get_plist(mod), "zathura", comment="PDF viewer", section="Documents"
    )
    apply_plan(plan, tmp_config)

    mod2 = get_module(tmp_config, "home/modules/apps.nix")
    plist = get_plist(mod2)
    assert "Documents" in [s.title for s in plist.sections]
    z = next(p for p in plist.packages if p.name == "zathura")
    assert z.section == "Documents"
    header = mod2.lines[z.line - 1]
    assert header.strip().startswith("# ── Documents ")
    assert "─" in header


def test_add_package_no_section(tmp_config):
    mod = get_module(tmp_config, "modules/nvidia.nix")
    plan = edits.add_package(mod, get_plist(mod), "vulkan-tools")
    apply_plan(plan, tmp_config)
    mod2 = get_module(tmp_config, "modules/nvidia.nix")
    assert "vulkan-tools" in [p.name for p in get_plist(mod2).packages]


def test_add_duplicate_package_rejected(tmp_config):
    mod = get_module(tmp_config, "home/modules/apps.nix")
    with pytest.raises(EditError, match="already"):
        edits.add_package(mod, get_plist(mod), "brave")


def test_file_still_loads_in_tree_after_edit(tmp_config):
    mod = get_module(tmp_config, "home/modules/apps.nix")
    plan = edits.add_package(mod, get_plist(mod), "firefox", section="Browsers")
    apply_plan(plan, tmp_config)
    tree = load_tree(tmp_config)  # whole tree still parses
    node = tree.find(tmp_config / "home" / "modules" / "apps.nix")
    assert "firefox" in [p.name for p in node.file.package_lists[0].packages]


# ── enable / disable / remove ────────────────────────────────────────────────

def test_disable_then_enable_package_roundtrip(tmp_config):
    rel = "modules/gaming.nix"
    mod = get_module(tmp_config, rel)
    plist = get_plist(mod)
    lutris = next(p for p in plist.packages if p.name == "lutris")
    original_line = mod.lines[lutris.line]

    apply_plan(edits.set_package_enabled(mod, lutris, False), tmp_config)
    mod2 = get_module(tmp_config, rel)
    lutris2 = next(p for p in get_plist(mod2).packages if p.name == "lutris")
    assert not lutris2.enabled
    assert lutris2.comment == lutris.comment  # inline comment survives

    apply_plan(edits.set_package_enabled(mod2, lutris2, True), tmp_config)
    mod3 = get_module(tmp_config, rel)
    lutris3 = next(p for p in get_plist(mod3).packages if p.name == "lutris")
    assert lutris3.enabled
    assert mod3.lines[lutris3.line] == original_line  # byte-identical roundtrip


def test_enable_disabled_package(tmp_config):
    rel = "home/modules/apps.nix"
    mod = get_module(tmp_config, rel)
    davinci = next(p for p in get_plist(mod).packages if p.name == "davinci-resolve")
    assert not davinci.enabled
    apply_plan(edits.set_package_enabled(mod, davinci, True), tmp_config)
    mod2 = get_module(tmp_config, rel)
    davinci2 = next(p for p in get_plist(mod2).packages if p.name == "davinci-resolve")
    assert davinci2.enabled


def test_remove_package(tmp_config):
    rel = "home/modules/apps.nix"
    mod = get_module(tmp_config, rel)
    before_count = len(get_plist(mod).packages)
    spotify = next(p for p in get_plist(mod).packages if p.name == "spotify")
    apply_plan(edits.remove_package(mod, spotify), tmp_config)
    mod2 = get_module(tmp_config, rel)
    names = [p.name for p in get_plist(mod2).packages]
    assert "spotify" not in names
    assert len(names) == before_count - 1


def test_remove_multiline_expr(tmp_config):
    rel = "home/modules/apps.nix"
    mod = get_module(tmp_config, rel)
    expr = next(p for p in get_plist(mod).packages if p.is_expr)
    apply_plan(edits.remove_package(mod, expr), tmp_config)
    mod2 = get_module(tmp_config, rel)
    assert not any(p.is_expr for p in get_plist(mod2).packages)
    assert "libreoffice" not in "\n".join(mod2.lines)


def test_read_only_module_rejected(tmp_config):
    mod = get_module(tmp_config, "hosts/nixos/hardware-configuration.nix")
    with pytest.raises(EditError, match="read-only"):
        edits.remove_package(
            mod,
            # any entry-shaped object; guard fires before it is used
            get_plist(get_module(tmp_config, "modules/gaming.nix")).packages[0],
        )


# ── imports ──────────────────────────────────────────────────────────────────

def test_toggle_import_roundtrip(tmp_config):
    rel = "hosts/nixos/default.nix"
    mod = get_module(tmp_config, rel)
    gaming = next(e for e in mod.imports_block.entries if "gaming" in e.raw)
    original = mod.lines[gaming.line]

    apply_plan(edits.set_import_enabled(mod, gaming, False), tmp_config)
    mod2 = get_module(tmp_config, rel)
    gaming2 = next(e for e in mod2.imports_block.entries if "gaming" in e.raw)
    assert not gaming2.enabled

    # Disabled module disappears from the resolved tree but stays listed.
    tree = load_tree(tmp_config)
    host = tree.system_roots[0]
    entry, child = next(c for c in host.children if "gaming" in c[0].raw)
    assert not entry.enabled and child is None

    apply_plan(edits.set_import_enabled(mod2, gaming2, True), tmp_config)
    mod3 = get_module(tmp_config, rel)
    gaming3 = next(e for e in mod3.imports_block.entries if "gaming" in e.raw)
    assert mod3.lines[gaming3.line] == original


def test_enable_commented_vm_module(tmp_config):
    rel = "hosts/nixos/default.nix"
    mod = get_module(tmp_config, rel)
    vm = next(e for e in mod.imports_block.entries if e.raw.endswith("vm.nix"))
    apply_plan(edits.set_import_enabled(mod, vm, True), tmp_config)
    tree = load_tree(tmp_config)
    rels = {n.file.rel for n in tree.all_nodes()}
    assert "modules/vm.nix" in rels


# ── create_module ────────────────────────────────────────────────────────────

def test_create_system_module(tmp_config):
    parent = get_module(tmp_config, "hosts/nixos/default.nix")
    new_path = tmp_config / "modules" / "firefox.nix"
    plan = edits.create_module(
        parent, new_path, "Firefox browser and related tools", "system"
    )
    apply_plan(plan, tmp_config)

    assert new_path.is_file()
    tree = load_tree(tmp_config)
    node = tree.find(new_path)
    assert node is not None and node.kind == "system"
    (plist,) = node.file.package_lists
    assert plist.attrpath == "environment.systemPackages"
    assert plist.packages == []

    # Import wired into the parent with the description as comment.
    parent2 = get_module(tmp_config, "hosts/nixos/default.nix")
    entry = next(
        e for e in parent2.imports_block.entries if e.raw.endswith("firefox.nix")
    )
    assert entry.raw == "../../modules/firefox.nix"
    assert entry.enabled


def test_create_home_module_and_add_package(tmp_config):
    parent = get_module(tmp_config, "home/radu.nix")
    new_path = tmp_config / "home" / "modules" / "firefox.nix"
    plan = edits.create_module(parent, new_path, "Firefox", "home")
    apply_plan(plan, tmp_config)

    mod = parse_module(new_path, tmp_config)
    (plist,) = mod.package_lists
    assert plist.attrpath == "home.packages"

    # The empty scaffold accepts a first package.
    plan2 = edits.add_package(mod, plist, "firefox", comment="Mozilla Firefox")
    Pipeline(tmp_config, validate=False, commit=False).apply(plan2)
    mod2 = parse_module(new_path, tmp_config)
    assert [p.name for p in mod2.package_lists[0].packages] == ["firefox"]


def test_create_module_existing_path_rejected(tmp_config):
    parent = get_module(tmp_config, "hosts/nixos/default.nix")
    with pytest.raises(EditError, match="exists"):
        edits.create_module(
            parent, tmp_config / "modules" / "gaming.nix", "dup", "system"
        )


# ── pipeline safety ──────────────────────────────────────────────────────────

def test_pipeline_diff_preview(tmp_config):
    mod = get_module(tmp_config, "home/modules/apps.nix")
    plan = edits.add_package(mod, get_plist(mod), "firefox", section="Browsers")
    diff = Pipeline(tmp_config, validate=False, commit=False).preview(plan)
    assert "+    firefox" in diff
    assert "apps.nix" in diff


def test_pipeline_rollback_restores_files(tmp_config, monkeypatch):
    import nixcfg.core.pipeline as pl

    mod = get_module(tmp_config, "home/modules/apps.nix")
    original = mod.text
    plan = edits.add_package(mod, get_plist(mod), "firefox", section="Browsers")

    pipe = Pipeline(tmp_config, validate=True, commit=False)
    monkeypatch.setattr(pipe, "nix_available", lambda: True)

    class FakeProc:
        returncode = 1
        stdout = ""
        stderr = "error: syntax error at line 3"

    monkeypatch.setattr(pl, "_run", lambda *a, **k: FakeProc())
    result = pipe.apply(plan)
    assert not result.ok
    assert result.rolled_back
    assert "syntax error" in result.output
    assert (tmp_config / "home/modules/apps.nix").read_text() == original


def test_pipeline_rollback_removes_created_files(tmp_config, monkeypatch):
    import nixcfg.core.pipeline as pl

    parent = get_module(tmp_config, "hosts/nixos/default.nix")
    parent_text = parent.text
    new_path = tmp_config / "modules" / "firefox.nix"
    plan = edits.create_module(parent, new_path, "Firefox", "system")

    pipe = Pipeline(tmp_config, validate=True, commit=False)
    monkeypatch.setattr(pipe, "nix_available", lambda: True)

    class FakeProc:
        returncode = 1
        stdout = ""
        stderr = "boom"

    monkeypatch.setattr(pl, "_run", lambda *a, **k: FakeProc())
    result = pipe.apply(plan)
    assert not result.ok and result.rolled_back
    assert not new_path.exists()
    assert (tmp_config / "hosts/nixos/default.nix").read_text() == parent_text


def test_pipeline_git_commit(tmp_config):
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=tmp_config, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_config, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
        cwd=tmp_config, check=True,
    )
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_config, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_config, check=True)

    mod = get_module(tmp_config, "home/modules/apps.nix")
    plan = edits.add_package(mod, get_plist(mod), "firefox", section="Browsers")
    result = Pipeline(tmp_config, validate=False, commit=True).apply(plan)
    assert result.ok and result.committed and result.commit_hash

    log = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"], cwd=tmp_config,
        capture_output=True, text=True,
    ).stdout.strip()
    assert log.startswith("nixcfg: add firefox")
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=tmp_config,
        capture_output=True, text=True,
    ).stdout.strip()
    assert status == ""  # nothing left uncommitted
