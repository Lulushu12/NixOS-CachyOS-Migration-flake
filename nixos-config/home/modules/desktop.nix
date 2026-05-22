{ pkgs, lib, ... }:

{
  # ── Qt theming ─────────────────────────────────────────────────────────────
  # GTK theming is left to KDE Plasma — it writes to ~/.gtkrc-2.0 and
  # ~/.config/gtk-{3,4}.0/ on every login, conflicting with HM symlinks.

  qt = {
    enable             = true;
    platformTheme.name = "kde";
    style = { name = "breeze"; package = pkgs.kdePackages.breeze; };
  };

  # ── Theme packages available in nixpkgs ────────────────────────────────────

  home.packages = with pkgs; [
    layan-kde          # Layan: Kvantum theme + color schemes + Aurorae decorations
    fluent-icon-theme  # Fluent / Fluent-dark icons
    kora-icon-theme    # kora icons
    tela-icon-theme    # Tela / Tela-dark icons
  ];

  # ── Custom themes NOT in nixpkgs ───────────────────────────────────────────
  # Copy your theme files into dotfiles/ first, then uncomment the blocks below.
  #
  # Color schemes  (Edna, Nordic, Otto, DankMatugen families):
  #   mkdir -p ../../dotfiles/themes/color-schemes
  #   cp ~/.local/share/color-schemes/{Edna,EdnaLight,Nordic,NordicDarker,Otto,OttoLight,DankMatugen,DankMatugenDark,DankMatugenLight}.colors \
  #      ../../dotfiles/themes/color-schemes/
  #
  # home.file.".local/share/color-schemes" = {
  #   source    = ../../dotfiles/themes/color-schemes;
  #   recursive = true;
  # };

  # Aurorae window decorations  (Edna, Nordic, Otto families):
  #   mkdir -p ../../dotfiles/themes/aurorae
  #   cp -r ~/.local/share/aurorae/themes/{Edna,Edna-Light,Nordic,Nordic-darker,Nordic-Solid,Otto,Otto-Light} \
  #      ../../dotfiles/themes/aurorae/
  #
  # home.file.".local/share/aurorae/themes" = {
  #   source    = ../../dotfiles/themes/aurorae;
  #   recursive = true;
  # };

  # Kvantum theme — Edna (the active theme; name is set in plasma.nix):
  #   mkdir -p ../../dotfiles/themes/kvantum
  #   cp -r ~/.config/Kvantum/Edna ../../dotfiles/themes/kvantum/
  #
  # xdg.configFile."Kvantum/Edna" = {
  #   source    = ../../dotfiles/themes/kvantum/Edna;
  #   recursive = true;
  # };

  # Icon themes NOT in nixpkgs  (McMojave-circle family, Nordic icon variants):
  #   mkdir -p ../../dotfiles/icons
  #   cp -r ~/.local/share/icons/{McMojave-circle,McMojave-circle-dark,McMojave-circle-light} \
  #      ../../dotfiles/icons/
  #   cp -r ~/.local/share/icons/{Nordic-bluish,Nordic-darker,Nordic-green} \
  #      ../../dotfiles/icons/
  #
  # home.file.".local/share/icons" = {
  #   source    = ../../dotfiles/icons;
  #   recursive = true;
  # };

  # ── Custom Plasma widgets (plasmoids) ──────────────────────────────────────
  # These are KDE Store widgets not packaged in nixpkgs.
  # Copy from your system first:
  #   mkdir -p ../../dotfiles/plasmoids
  #   cp -r ~/.local/share/plasma/plasmoids/{AndromedaLauncher,luisbocanegra.audio.visualizer,luisbocanegra.panel.colorizer,plasmusic-toolbar,KdeControlStation,zayron.simple.separator} \
  #      ../../dotfiles/plasmoids/
  #
  # home.file.".local/share/plasma/plasmoids" = {
  #   source    = ../../dotfiles/plasmoids;
  #   recursive = true;
  # };
}
