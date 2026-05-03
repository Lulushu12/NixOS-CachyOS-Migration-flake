# NVIDIA proprietary driver configuration.
#
# ─── GPU compatibility ────────────────────────────────────────────────────────
# open = true  → NVIDIA open-source kernel modules (Turing / RTX 20xx and newer)
# open = false → proprietary kernel modules (required for GTX 10xx and older)
#
# ─── After first rebuild ─────────────────────────────────────────────────────
# Verify the driver loaded correctly:
#   nvidia-smi
#   glxinfo | grep "OpenGL renderer"
#
# ─── KDE Plasma Wayland + NVIDIA ─────────────────────────────────────────────
# modesetting.enable = true is required for Wayland.
# If you see flickering or black screens under Plasma Wayland, try adding:
#   environment.sessionVariables.KWIN_DRM_USE_EGL_STREAMS = "1";
# or switch to the Plasma (X11) session as a fallback.

{ config, pkgs, ... }:

{
  # Load the NVIDIA driver for Xorg and Wayland
  services.xserver.videoDrivers = [ "nvidia" ];

  hardware.nvidia = {
    modesetting.enable = true;

    # Fine-grained power management — only for laptops with hybrid GPU (Optimus).
    # Disable on desktops.
    powerManagement.enable = false;
    powerManagement.finegrained = false;

    # Open-source kernel modules (Turing / RTX 20xx+).
    # Set to false if you have a GTX 10xx or older GPU.
    open = true;

    # Install nvidia-settings GUI
    nvidiaSettings = true;

    # Use the stable driver. Alternatives: beta, production, legacy_*
    package = config.boot.kernelPackages.nvidiaPackages.stable;
  };

  # VA-API hardware video decode (equivalent to libva-nvidia-driver on Arch)
  hardware.graphics.extraPackages = with pkgs; [
    nvidia-vaapi-driver
  ];


  environment.systemPackages = with pkgs; [
    nvtopPackages.nvidia  # GPU monitoring (htop for your GPU)
  ];
}
