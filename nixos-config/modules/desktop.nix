# Desktop environment: KDE Plasma 6.
#
# ─── Session selection ────────────────────────────────────────────────────────
# At the SDDM login screen:
#   • "Plasma (Wayland)" → KDE Plasma 6 on Wayland (recommended)
#   • "Plasma (X11)"     → KDE Plasma 6 on X11 (compatibility fallback)
#
# ─── Bare metal note ─────────────────────────────────────────────────────────
# On bare metal, Plasma (Wayland) is the preferred session.
# If you experience GPU issues, fall back to Plasma (X11) at the login screen.

{ pkgs, ... }:

{
  # ── OpenRGB (RGB lighting control) ────────────────────────────────────────
  # Installs OpenRGB and sets up udev rules for device access.
  services.hardware.openrgb.enable = true;

  # ── DDC/CI monitor control (ddcutil) ─────────────────────────────────────
  # Enables i2c-dev kernel module and grants the user i2c group access,
  # which ddcutil needs to communicate with monitors over DDC/CI.
  hardware.i2c.enable = true;
  # ── Login manager (SDDM) ───────────────────────────────────────────────────
  services.displayManager.sddm.enable = true;
  services.displayManager.defaultSession = "plasma";

  # ── KDE Plasma 6 ───────────────────────────────────────────────────────────
  services.desktopManager.plasma6.enable = true;

  # ── X server ───────────────────────────────────────────────────────────────
  # Required for KDE's X11 session and XWayland (runs X11 apps inside Wayland).
  services.xserver = {
    enable = true;
    xkb.layout  = "us";
    xkb.variant = "";
  };

  # ── XDG desktop portals ────────────────────────────────────────────────────
  xdg.portal = {
    enable = true;
    extraPortals = [ pkgs.kdePackages.xdg-desktop-portal-kde ];
    config.common.default = [ "kde" ];
  };

  # ── System packages ────────────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [

    # ── KDE applications ──────────────────────────────────────────────────
    kdePackages.kate            # Text editor
    kdePackages.kcalc           # Calculator
    kdePackages.ark             # Archive manager (zip, tar, 7z, etc.)
    kdePackages.filelight       # Visual disk usage
    kdePackages.dolphin         # File manager
    kdePackages.gwenview        # Image viewer
    kdePackages.spectacle       # Screenshot tool
    kdePackages.kdeconnect-kde  # Phone integration (KDE Connect)
    kdePackages.korganizer      # Calendar and task manager
    kdePackages.partitionmanager # Partition editor
    qt6Packages.qtstyleplugin-kvantum  # Kvantum Qt theme engine (Qt6)
    kdePackages.kcolorchooser   # Color picker utility
    kdePackages.kinfocenter     # System information viewer
    kdePackages.dolphin-plugins # Git status, audio tagging, etc. in Dolphin
    kdePackages.wacomtablet     # Wacom drawing tablet configuration

    # ── Wallpaper ─────────────────────────────────────────────────────────
    # Requires Wallpaper Engine purchased on Steam.
    # Note: reports of crashes on Plasma 6.5+ / Qt 6.10 — upstream inactive.
    kdePackages.wallpaper-engine-plugin

    # ── KWin effects ──────────────────────────────────────────────────────
    kde-rounded-corners  # Third-party rounded corners (matinlotfali/KDE-Rounded-Corners)

    # ── Codecs / media ────────────────────────────────────────────────────
    gst_all_1.gst-plugins-bad   # GStreamer extra codecs (used by KDE/Qt apps)
    gst_all_1.gst-plugins-ugly  # GStreamer patent-encumbered codecs (MP3, etc.)
    gst_all_1.gst-libav         # GStreamer FFmpeg bridge (broad format support)
    ffmpegthumbnailer            # Video thumbnails in Dolphin
    libdvdcss                    # DVD decryption (for VLC playback)

    # ── Network ───────────────────────────────────────────────────────────
    networkmanager-openvpn       # OpenVPN plugin for NetworkManager / KDE applet

    # ── Hardware ──────────────────────────────────────────────────────────
    ddcutil   # Control monitor brightness/input via DDC/CI (needs hardware.i2c above)

    # ── Clipboard ─────────────────────────────────────────────────────────
    wl-clipboard    # `wl-copy` / `wl-paste` — Wayland clipboard CLI

    # ── Media controls ────────────────────────────────────────────────────
    playerctl       # CLI media control (play/pause/next via keybindings)
    pavucontrol     # PipeWire/PulseAudio volume control GUI

    # ── Brightness ────────────────────────────────────────────────────────
    brightnessctl   # Screen brightness control (laptops)

    # ── General Wayland / Qt support ──────────────────────────────────────
    xdg-utils       # `xdg-open` file association handling
    qt6.qtwayland   # Qt 6 Wayland platform plugin
    libsForQt5.qt5ct # Qt 5 style configurator

  ];

  # ── Qt platform theme ──────────────────────────────────────────────────────
  qt = {
    enable        = true;
    platformTheme = "kde";
    style         = "breeze";
  };
}
