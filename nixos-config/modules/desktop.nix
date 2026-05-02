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
    kdePackages.kvantum         # Qt theme engine (custom themes)

    # ── Wallpaper ─────────────────────────────────────────────────────────
    # Requires Wallpaper Engine purchased on Steam.
    # Note: reports of crashes on Plasma 6.5+ / Qt 6.10 — upstream inactive.
    kdePackages.wallpaper-engine-plugin

    # ── KWin effects ──────────────────────────────────────────────────────
    kde-rounded-corners  # Third-party rounded corners (matinlotfali/KDE-Rounded-Corners)

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
