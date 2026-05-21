{ pkgs, ... }:

# Wayland compositor stack: wofi launcher, mako notifications,
# waybar status bar, and niri compositor.
# All are stubbed — share your config files to fill each section in.

{
  # ── Wofi (app launcher) ────────────────────────────────────────────────────
  # settings: share ~/.config/wofi/ to fill this in

  programs.wofi.enable = true;

  # xdg.configFile."wofi/style.css".source = ../../dotfiles/wayland/wofi/style.css;

  # ── Mako (notification daemon) ────────────────────────────────────────────
  # TODO: share ~/.config/mako/config to fill this in
  #
  # services.mako = {
  #   enable = true;
  #   # Example options:
  #   # defaultTimeout = 5000;
  #   # backgroundColor = "#1a1b26";
  #   # textColor = "#c0caf5";
  # };

  # ── Waybar (status bar) ───────────────────────────────────────────────────
  # TODO: share ~/.config/waybar/ to fill this in
  #
  # programs.waybar = {
  #   enable = true;
  #   settings = { };  # paste your config.jsonc content here as Nix attrset
  #   style = "";      # paste your style.css here
  # };

  # ── Niri (Wayland compositor) ─────────────────────────────────────────────
  # TODO: share ~/.config/niri/config.kdl to fill this in
  #
  # wayland.windowManager.niri = {
  #   enable   = true;
  #   settings = { };  # niri-specific settings attrset
  # };

  # ── Wlogout ───────────────────────────────────────────────────────────────
  # xdg.configFile."wlogout".source = ../../dotfiles/wayland/wlogout;
}
