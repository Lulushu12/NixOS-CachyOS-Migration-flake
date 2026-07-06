from pathlib import Path

import pytest

from nixcfg.core.graph import ConfigError, find_flake_root, load_tree


def test_find_flake_root_variants(real_config):
    assert find_flake_root(real_config) == real_config
    assert find_flake_root(real_config / "flake.nix") == real_config
    assert find_flake_root(real_config / "modules") == real_config
    # Repo root: finds the nested nixos-config/ automatically.
    assert find_flake_root(real_config.parent) == real_config


def test_find_flake_root_missing(tmp_path):
    with pytest.raises(ConfigError):
        find_flake_root(tmp_path)


def test_tree_roots(real_config):
    tree = load_tree(real_config)
    assert [n.file.rel for n in tree.system_roots] == ["hosts/nixos/default.nix"]
    assert [n.file.rel for n in tree.home_roots] == ["home/radu.nix"]
    assert all(n.kind == "system" for n in tree.system_roots)
    assert all(n.kind == "home" for n in tree.home_roots)


def test_tree_children_include_disabled(real_config):
    tree = load_tree(real_config)
    host = tree.system_roots[0]
    by_raw = {entry.raw: (entry, child) for entry, child in host.children}

    entry, child = by_raw["../../modules/gaming.nix"]
    assert entry.enabled and child is not None
    assert child.file.rel == "modules/gaming.nix"

    entry, child = by_raw["../../modules/vm.nix"]
    assert not entry.enabled and child is None  # disabled: shown, not descended


def test_home_tree_children(real_config):
    tree = load_tree(real_config)
    home = tree.home_roots[0]
    rels = [c.file.rel for _, c in home.children if c is not None]
    assert "home/modules/apps.nix" in rels
    assert "home/modules/shell.nix" in rels


def test_all_nodes_walks_everything(real_config):
    tree = load_tree(real_config)
    rels = {n.file.rel for n in tree.all_nodes()}
    assert "modules/gaming.nix" in rels
    assert "modules/nvidia.nix" in rels
    assert "home/modules/apps.nix" in rels
    assert "hosts/nixos/hardware-configuration.nix" in rels


def test_find_by_path(real_config):
    tree = load_tree(real_config)
    node = tree.find(real_config / "modules" / "gaming.nix")
    assert node is not None and node.kind == "system"
