from nixcfg.core.parser import parse_module


def test_gaming_module_packages_and_sections(real_config):
    mod = parse_module(real_config / "modules" / "gaming.nix", real_config)
    (plist,) = mod.package_lists
    assert plist.attrpath == "environment.systemPackages"
    assert plist.with_pkgs

    names = [p.name for p in plist.packages if not p.is_expr]
    assert "lutris" in names
    assert "mangohud" in names

    lutris = next(p for p in plist.packages if p.name == "lutris")
    assert lutris.section == "Launchers & managers"
    assert lutris.enabled
    assert "GOG" in lutris.comment

    titles = [s.title for s in plist.sections]
    assert "Launchers & managers" in titles
    assert "Performance overlay" in titles


def test_gaming_module_options(real_config):
    mod = parse_module(real_config / "modules" / "gaming.nix", real_config)
    opts = {o.attrpath: o for o in mod.options}
    assert opts["programs.steam.enable"].value == "true"
    assert opts["programs.steam.enable"].simple
    assert opts["programs.gamemode.enable"].value == "true"
    assert opts["hardware.graphics.enable32Bit"].value == "true"


def test_nested_option_paths(real_config):
    mod = parse_module(real_config / "modules" / "nvidia.nix", real_config)
    opts = {o.attrpath: o for o in mod.options}
    assert opts["hardware.nvidia.modesetting.enable"].value == "true"
    assert opts["hardware.nvidia.open"].value == "true"
    # Non-scalar value → present but not editable.
    assert not opts["hardware.nvidia.package"].simple


def test_host_imports_with_disabled_entries(real_config):
    mod = parse_module(real_config / "hosts" / "nixos" / "default.nix", real_config)
    block = mod.imports_block
    assert block is not None
    by_raw = {e.raw: e for e in block.entries}

    gaming = by_raw["../../modules/gaming.nix"]
    assert gaming.enabled
    assert gaming.resolved is not None and gaming.resolved.name == "gaming.nix"

    vm = by_raw["../../modules/vm.nix"]
    assert not vm.enabled
    assert vm.resolved is not None  # file exists, import just commented out


def test_disabled_package_detected_but_not_prose(real_config):
    mod = parse_module(real_config / "home" / "modules" / "apps.nix", real_config)
    (plist,) = mod.package_lists
    disabled = [p.name for p in plist.packages if not p.enabled]
    assert "davinci-resolve" in disabled

    # The desktop module is full of prose comment blocks — none of them
    # may be misread as packages.
    desktop = parse_module(real_config / "home" / "modules" / "desktop.nix", real_config)
    (dlist,) = desktop.package_lists
    names = {p.name for p in dlist.packages}
    assert names == {"layan-kde", "fluent-icon-theme", "kora-icon-theme", "tela-icon-theme"}


def test_parenthesized_expression_entry(real_config):
    mod = parse_module(real_config / "home" / "modules" / "apps.nix", real_config)
    (plist,) = mod.package_lists
    exprs = [p for p in plist.packages if p.is_expr]
    assert len(exprs) == 1
    assert "libreoffice-fresh" in exprs[0].name
    assert exprs[0].comment.startswith("tests skipped")
    assert exprs[0].section == "Productivity"


def test_hardware_configuration_read_only(real_config):
    mod = parse_module(
        real_config / "hosts" / "nixos" / "hardware-configuration.nix", real_config
    )
    assert mod.read_only


def test_dotted_package_names(real_config):
    mod = parse_module(real_config / "home" / "modules" / "apps.nix", real_config)
    (plist,) = mod.package_lists
    assert "kdePackages.kdenlive" in [p.name for p in plist.packages]
