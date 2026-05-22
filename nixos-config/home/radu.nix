{ pkgs, config, ... }:

{
  home.stateVersion  = "24.11";
  home.username      = "radu";
  home.homeDirectory = "/home/radu";

  imports = [
    ./modules/shell.nix
    ./modules/terminal.nix
    ./modules/development.nix
    ./modules/desktop.nix
    ./modules/plasma.nix
    ./modules/apps.nix
    ./modules/wayland.nix
  ];

  # ── Session environment variables ──────────────────────────────────────────
  home.sessionVariables = {
    EDITOR  = "kate";
    VISUAL  = "kate";
    BROWSER = "brave";
    NIXOS_OZONE_EL     = "1";  # Native Wayland for Electron apps (Obsidian, etc.)
    MOZ_ENABLE_WAYLAND = "1";  # Native Wayland for Firefox-based browsers
    QT_QPA_PLATFORM    = "wayland;xcb";
  };

  # Propagate the Nix profile PATH into the systemd user environment so that
  # desktop-launched apps (e.g. Claude Desktop spawning claude-code) can find
  # binaries that are only in the user profile, not the system PATH.
  systemd.user.sessionVariables = {
    PATH = "${config.home.profileDirectory}/bin:$PATH";
  };

  programs.home-manager.enable = true;
}
