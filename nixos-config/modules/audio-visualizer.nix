# Audio visualizer support module.
#
# Provides the system-level dependencies required by the
# luisbocanegra.audio.visualizer KDE Plasma widget.  The widget's
# commandMonitor script communicates with PipeWire via:
#   • pactl   — enumerate sinks/sources, switch audio ports (pulseaudio pkg)
#   • amixer  — mute/unmute the headphone jack (alsa-utils pkg)
#   • python3 — WebSocket server that streams PCM/FFT data to the widget
#
# The Python environment below ships websockets (the server transport)
# and dbus-python (for DBus-based media metadata queries).  Both must be
# present in the *system* Python so the widget's shebang
# (#!/usr/bin/env python3) resolves to an interpreter that can import them.
#
# After rebuilding, verify the widget works by launching it in the Plasma
# panel; no shebang patching is needed once this module is active.

{ pkgs, ... }:

{
  environment.systemPackages = with pkgs; [

    # ── PulseAudio CLI tools ───────────────────────────────────────────────
    # PipeWire ships a fully compatible pactl/pacmd layer, so installing the
    # pulseaudio package here only brings in the CLI binaries — it does NOT
    # start the PulseAudio daemon (which remains disabled in common.nix).
    pulseaudio   # pactl, pacmd — audio port & sink control

    # ── ALSA utilities ────────────────────────────────────────────────────
    alsa-utils   # amixer, alsamixer — jack-level muting, mixer control

    # ── Python + required libraries ───────────────────────────────────────
    # A self-contained Python environment so that `python3` on PATH always
    # has websockets and dbus-python available, regardless of any virtualenv.
    (python3.withPackages (ps: with ps; [
      websockets   # WebSocket server transport for the visualizer widget
      dbus-python  # DBus bindings for media metadata (MPRIS, etc.)
    ]))

  ];
}
