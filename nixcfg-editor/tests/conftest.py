import shutil
from pathlib import Path

import pytest

REPO_CONFIG = Path(__file__).resolve().parents[2] / "nixos-config"


@pytest.fixture
def real_config() -> Path:
    """The repo's actual nixos-config, read-only tests only."""
    assert (REPO_CONFIG / "flake.nix").is_file()
    return REPO_CONFIG


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    """A disposable copy of the real config for edit tests."""
    dest = tmp_path / "nixos-config"
    shutil.copytree(REPO_CONFIG, dest)
    return dest
