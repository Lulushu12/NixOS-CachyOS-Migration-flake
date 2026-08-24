# Android screen mirroring module.
#
# Mirrors (and optionally controls) an Android phone's screen on the desktop
# using scrcpy, which streams the display over the Android Debug Bridge (ADB).
# No app is needed on the phone — only USB debugging (or wireless debugging).
#
# What this module wires up:
#   • programs.adb.enable — installs android-tools (adb), creates the `adbusers`
#     group, and installs the udev rules that give that group access to
#     Android devices over USB. Without these rules, `adb devices` shows the
#     phone as "no permissions".
#   • scrcpy — the actual mirroring client (video + audio + input forwarding).
#   • radu is added to `adbusers` so USB access works without sudo. This list
#     is merged with the extraGroups defined in hosts/nixos/default.nix.
#
# ── One-time phone setup ───────────────────────────────────────────────────────
#   1. Settings → About phone → tap "Build number" 7× to unlock Developer options.
#   2. Settings → System → Developer options → enable "USB debugging".
#   3. Plug the phone in with a data-capable USB cable. Run `adb devices` and
#      accept the "Allow USB debugging?" prompt on the phone (tick "always
#      allow" for this computer).
#
# ── Usage ──────────────────────────────────────────────────────────────────────
#   scrcpy                       # mirror over USB
#   scrcpy --turn-screen-off     # mirror but keep the phone's own screen off
#   scrcpy --no-control          # view-only, ignore mouse/keyboard input
#   scrcpy -m 1024 -b 8M         # cap resolution to 1024px, bitrate to 8 Mbit/s
#
# ── Wireless (no cable) ────────────────────────────────────────────────────────
#   Plug in once, then:
#     adb tcpip 5555                       # switch the phone's adb to TCP/IP
#     adb connect <phone-ip>:5555          # (find the IP in Wi-Fi settings)
#   Unplug the cable and run `scrcpy` as usual. On Android 11+ you can skip the
#   cable entirely via Developer options → "Wireless debugging" and
#   `adb pair <ip>:<port>`.
#
# After rebuilding you must log out and back in once so the new `adbusers`
# group membership takes effect.

{ pkgs, ... }:

{
  # Enables adb + sets up the udev rules and `adbusers` group.
  programs.adb.enable = true;

  # scrcpy is the mirroring client; it depends on the adb from programs.adb.
  environment.systemPackages = with pkgs; [
    scrcpy   # low-latency Android display mirroring & control
  ];

  # Grant radu USB access to Android devices without sudo. Merged with the
  # extraGroups list in hosts/nixos/default.nix.
  users.users.radu.extraGroups = [ "adbusers" ];
}
