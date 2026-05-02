# Claude Desktop — installed via community flake (not in nixpkgs).
# Source: github:k3d3/claude-desktop-linux-flake
#
# The flake input is declared in flake.nix and passed here via specialArgs.
# Config and conversation data live in ~/.config/Claude/ — survives rebuilds.

{ inputs, ... }:

{
  home-manager.users.radu = {
    home.packages = [
      inputs.claude-desktop.packages.x86_64-linux.claude-desktop
    ];
  };
}
