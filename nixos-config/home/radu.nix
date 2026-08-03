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
    ./modules/jarvis.nix
  ];

  # ── Voice assistant ────────────────────────────────────────────────────────
  # The speech services and local model are system-level (modules/jarvis.nix);
  # this configures the orchestrator that drives them. Full option reference and
  # setup notes: JARVIS.md at the repo root.
  services.jarvis = {
    enable        = true;
    userName      = "Radu";
    assistantName = "JARVIS";

    # Tone and standing preferences. This is the whole personality knob.
    personality = ''
      Be dry, precise, and unhurried. Skip pleasantries and filler — no "certainly",
      no "I'd be happy to". A little sardonic is welcome; enthusiasm is not.
      If a request is ambiguous in a way that changes what you would do, ask.
      Otherwise pick the sensible reading and act.
    '';
  };

  # ── Session environment variables ──────────────────────────────────────────
  home.sessionVariables = {
    EDITOR  = "kate";
    VISUAL  = "kate";
    BROWSER = "brave";
    NIXOS_OZONE_WL     = "1";  # Native Wayland for Electron apps (Obsidian, Antigravity, etc.)
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
