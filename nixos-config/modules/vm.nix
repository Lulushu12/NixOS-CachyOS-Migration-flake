# QEMU / KVM guest tools with SPICE display protocol.
#
# ─── Which hypervisor are you using? ────────────────────────────────────────
# • QEMU/KVM (virt-manager, Proxmox, etc.) → import this file (default)
# • VirtualBox                              → swap to modules/virtualbox.nix
#   in hosts/nixos/default.nix
#
# What SPICE gives you inside the VM:
#   • Auto-resize: the VM display adapts when you resize the window on the host
#   • Shared clipboard between host and guest (enable SPICE channel in the
#     hypervisor settings under "Display → SPICE")
#   • USB device redirection (optional, needs SPICE USB channel enabled)
#
# What the QEMU guest agent adds:
#   • Clean shutdown / reboot from the hypervisor UI
#   • Freeze-consistent snapshots while the VM is running
#   • Memory balloon device support (dynamic memory adjustment)
#
# ─── virt-manager quick setup ────────────────────────────────────────────────
# When creating the VM, under "Display":
#   Type      → SPICE
#   Listen    → None (for local use)
# Under "Video":
#   Model     → VirtIO  (best performance, supports 3D acceleration)
# Under "Sound":
#   Model     → ich9 or virtio  (both work with PipeWire)

{ pkgs, lib, ... }:

{
  # QEMU guest agent — hypervisor ↔ VM coordination
  services.qemuGuest.enable = true;

  # SPICE agent — clipboard sharing and dynamic screen resolution
  services.spice-vdagentd.enable = true;

  # VirtIO GPU kernel module.
  # Without this, Niri (and any DRM/KMS compositor) gets driver=(null) on
  # /dev/dri/card0, EGL_EXT_device_drm is unsupported, and the display
  # backend fails to initialise — resulting in a black screen with no output.
  boot.kernelModules = [ "virtio_gpu" ];

  # Mesa OpenGL drivers for the VirtIO GPU.
  # Enables DRI and the Gallium VirtIO driver so EGL/Vulkan work inside
  # the VM, which is required for Wayland compositors like Niri.
  hardware.graphics.enable = true;

  # VirtIO GPU without VirGL 3D does not expose EGL_EXT_device_drm, so
  # Niri's TTY/KMS backend cannot initialise. Instead, register a custom
  # X11 session that launches Niri via its winit backend (nested under
  # SDDM's X11 server). DISPLAY is already set by SDDM, so Niri detects
  # it automatically and skips the TTY backend entirely.
  services.displayManager.sessionPackages = let
    # pkgs.writeText strips common leading indentation from the Nix ''...''
    # string, producing a properly-formatted .desktop file with no leading
    # whitespace — required for the [Desktop Entry] header to be recognised.
    desktopFile = pkgs.writeText "niri-x11.desktop" ''
      [Desktop Entry]
      Name=Niri
      Comment=Niri scrollable-tiling Wayland compositor (nested under KWin)
      Exec=kwin_wayland --no-global-shortcuts --no-kactivities --no-lockscreen -- niri
      Type=Application
      DesktopNames=niri
    '';
  in [
    (pkgs.runCommand "niri-x11-session" {
      passthru.providedSessions = [ "niri-x11" ];
    } ''
      mkdir -p $out/share/xsessions
      cp ${desktopFile} $out/share/xsessions/niri-x11.desktop
    '')
  ];

  # Override the default session set in desktop.nix to use the X11-nested
  # Niri session instead of the TTY-backed wayland session.
  services.displayManager.defaultSession = lib.mkForce "niri-x11";

  environment.systemPackages = [
    pkgs.spice-vdagent  # User-space SPICE agent (clipboard, resize)
  ];
}
