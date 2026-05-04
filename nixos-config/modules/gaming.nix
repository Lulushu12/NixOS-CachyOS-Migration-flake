# Gaming stack: Steam + Proton, Lutris, GameMode, MangoHud, RetroArch.
#
# ─── Quick-start Steam setup ─────────────────────────────────────────────────
# 1. Launch Steam and sign in
# 2. Enable Proton for all games:
#      Steam → Settings → Compatibility → Enable Steam Play for all titles
# 3. Install Proton-GE (better compatibility than stock Proton):
#      Launch `protonup-qt` from the app menu and install the latest GE-Proton
# 4. Per-game launch options for best performance:
#      MANGOHUD=1 gamemoderun %command%
#    (shows overlay + activates CPU/GPU optimisations while the game runs)
#
# ─── Note on GPU passthrough ─────────────────────────────────────────────────
# In a VM without GPU passthrough, 3D games will use software rendering
# (llvmpipe / lavapipe). Performance will be poor for modern 3D titles.
# Steam, Lutris, RetroArch, and 2D/light games will all work fine.
# Full gaming performance requires either:
#   a) A dedicated GPU passed through to the VM (VFIO/IOMMU)
#   b) Bare-metal installation

{ pkgs, ... }:

{
  # ── Steam ──────────────────────────────────────────────────────────────────
  programs.steam = {
    enable = true;
    remotePlay.openFirewall    = true;   # Steam Remote Play (streaming to other devices)
    dedicatedServer.openFirewall = false; # Source game dedicated servers — enable if needed
  };

  # ── GameMode ───────────────────────────────────────────────────────────────
  # Temporarily tweaks the system while a game runs:
  #   • CPU governor → performance
  #   • Scheduler → game-friendly
  #   • Inhibits power saving
  # Activate per-game with `gamemoderun %command%` in Steam launch options.
  programs.gamemode.enable = true;

  # ── 32-bit GPU / graphics support ─────────────────────────────────────────
  # Required for 32-bit games (via Steam/Proton) and Wine applications.
  hardware.graphics = {
    enable      = true;
    enable32Bit = true;
  };

  # ── System packages ────────────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [

    # ── Launchers & managers ────────────────────────────────────────────────
    lutris               # GOG, Epic, Battle.net, emulators, custom installers
    heroic               # Native GOG and Epic Games launcher (polished GUI)
    bottles              # Run Windows games/apps in isolated Wine prefixes
    protonup-qt          # GUI tool to install and manage Proton-GE versions

    # ── Performance overlay ─────────────────────────────────────────────────
    mangohud             # In-game overlay: FPS, CPU, GPU, VRAM, temps
    goverlay             # GUI configurator for MangoHud profiles

    # ── Wine ────────────────────────────────────────────────────────────────
    # wineWowPackages.waylandFull installs both 64-bit and 32-bit Wine
    # with native Wayland support — best choice for a Wayland desktop.
    wineWowPackages.waylandFull
    winetricks           # Install Windows runtimes (DirectX, .NET, VCRedist…)

    # ── Emulation ───────────────────────────────────────────────────────────
    retroarch            # Multi-system emulator front end
    libretro.snes9x      # Super Nintendo / Super Famicom
    libretro.mgba        # Game Boy / Game Boy Color / Game Boy Advance
    libretro.ppsspp      # PlayStation Portable
    libretro.dolphin     # GameCube and Wii
    libretro.desmume     # Nintendo DS
    # More cores available — add them here or download via RetroArch's Online Updater

    # ── Controller support ──────────────────────────────────────────────────
    antimicrox           # Map controller buttons/axes to keyboard or mouse
    evtest               # CLI tool: test joystick/controller input events

  ];
}
