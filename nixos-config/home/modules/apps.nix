{ pkgs, ... }:

{
  home.packages = with pkgs; [

    # ── Browsers ──────────────────────────────────────────────────────────────
    brave
    vivaldi
    mullvad-browser

    # ── Multimedia ────────────────────────────────────────────────────────────
    vlc
    spotify
    gimp
    inkscape-with-extensions
    kdePackages.kdenlive
    blender
    # davinci-resolve  # uncomment on bare metal with working GPU driver

    # ── Communication ─────────────────────────────────────────────────────────
    vesktop
    discord

    # ── Productivity ──────────────────────────────────────────────────────────
    (libreoffice-fresh.overrideAttrs (_: { doCheck = false; }))  # tests skipped: upstream sd_export_tests flaky
    obsidian

    # ── Remote / cloud ────────────────────────────────────────────────────────
    anydesk
    rclone

    # ── Creative / CAD ────────────────────────────────────────────────────────
    freecad
    onlyoffice-desktopeditors

  ];

  # ── MPV ───────────────────────────────────────────────────────────────────

  programs.mpv = {
    enable = true;
    config = {
      profile               = "gpu-hq";
      vo                    = "gpu";
      hwdec                 = "auto-safe";
      sub-auto              = "fuzzy";
      volume                = 75;
      save-position-on-quit = true;
    };
  };

  # ── OBS Studio ────────────────────────────────────────────────────────────
  # settings: share ~/.config/obs-studio/ to fill this in

  programs.obs-studio.enable = true;

  # ── Music players ─────────────────────────────────────────────────────────
  # settings: share ~/.config/spotify-player/ and ~/.config/ncspot/ to fill in

  programs.spotify-player.enable = true;
  programs.ncspot.enable         = true;

  # ── RetroArch ─────────────────────────────────────────────────────────────
  # settings: share ~/.config/retroarch/ to fill this in

  programs.retroarch.enable = true;

  # ── Apps without a Home Manager module (xdg.configFile) ───────────────────
  # Uncomment each block after copying the config file into dotfiles/.

  # Vesktop (Discord client):
  #   mkdir -p ../../dotfiles/apps
  #   cp ~/.config/vesktop/settings.json ../../dotfiles/apps/vesktop-settings.json
  #
  # xdg.configFile."vesktop/settings.json".source = ../../dotfiles/apps/vesktop-settings.json;

  # VLC:
  #   cp ~/.config/vlc/vlcrc ../../dotfiles/apps/vlcrc
  #
  # xdg.configFile."vlc/vlcrc".source = ../../dotfiles/apps/vlcrc;

  # qBittorrent:
  #   cp ~/.config/qBittorrent/qBittorrent.conf ../../dotfiles/apps/qbittorrent.conf
  #
  # xdg.configFile."qBittorrent/qBittorrent.conf".source = ../../dotfiles/apps/qbittorrent.conf;
}
