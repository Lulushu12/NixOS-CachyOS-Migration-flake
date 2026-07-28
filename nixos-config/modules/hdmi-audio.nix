# HDMI audio tuning — fixes audio that lags behind the picture on a TV.
#
# Symptom: plug the PC into the TV over HDMI, and the sound arrives roughly a
# second after the image.  There are three independent causes, and they need
# different fixes.  This module handles all three.
#
#   1. Node suspend.  WirePlumber powers HDMI sinks down after a few seconds
#      of silence.  Waking the codec back up takes time, so the first part of
#      every sound is late or clipped.  Fixed here by never suspending HDMI
#      sinks (session.suspend-timeout-seconds = 0).
#
#   2. ALSA buffering.  If PipeWire negotiates a large period with the HDMI
#      device, everything queued in that buffer plays late.  Fixed here by
#      pinning a small, explicit period on HDMI nodes.
#
#   3. TV-side processing.  This is the big one, and it is almost certainly
#      the cause of a delay as large as a second.  The TV buffers and
#      processes audio internally (and again in a soundbar, if audio is
#      passed through over ARC/eARC).  Linux cannot make that buffer smaller
#      — but it can *declare* it, so players know to hold the video back by
#      the same amount and lip sync is restored.  That is what
#      `tvAudioDelayMs` below does.  It is the one value you have to measure.
#
# ─── How to measure and set the delay ────────────────────────────────────────
#
#   1. Play a video on the TV with mpv (any talking-head clip works):
#        mpv --audio-device=pulse yourvideo.mp4
#
#   2. Press Ctrl+minus / Ctrl+plus to shift audio until lips match.  mpv
#      prints the value it settled on, e.g. "Audio delay: -0.900".
#
#   3. Take the absolute value in milliseconds — 0.900 → 900 — and set it as
#      `tvAudioDelayMs` below, then rebuild:
#        sudo nixos-rebuild switch --flake /etc/nixos/nixos-config#nixos
#
#   4. Log out and back in (or `systemctl --user restart wireplumber`) so the
#      HDMI node is recreated with the new value, then check it applied:
#        hdmi-audio-info
#
# A negative mpv delay means audio is late (the normal TV case) and is what
# this setting corrects.  If mpv wanted a *positive* delay, audio is running
# early instead — leave this at 0 and use the TV's own "audio delay" /
# "lip sync" slider, which can only push audio later.
#
# ─── Try the TV's own settings first ─────────────────────────────────────────
#
# Before dialling in a compensation value, these usually cut the delay a lot:
#   • Enable Game Mode, or label the HDMI input "PC" — both disable the
#     motion-smoothing/upscaling pipeline that causes most of the delay.
#   • Turn off any "surround", "virtual surround" or night-mode DSP effect.
#   • If sound goes out to a soundbar or receiver over ARC/eARC, test with the
#     TV's own speakers to see how much of the delay the passthrough adds.
#
# Cause 3 lives in the TV, so it is worth fixing there before compensating for
# it here: a TV in Game Mode delays everything less, including games where
# audio compensation cannot help because there is no video stream to hold back.

{ pkgs, ... }:

let
  # ── TUNABLE: TV audio delay compensation, in milliseconds ──────────────────
  # 0 = no compensation.  Set this to the delay you measured with mpv above.
  # Typical TVs land between 100 and 250 ms; a full second usually means the
  # TV is doing heavy video processing, so try Game Mode before trusting it.
  tvAudioDelayMs = 0;

  # Matches the HDMI output nodes PipeWire creates for the GPU's audio
  # function, e.g. "alsa_output.pci-0000_09_00.1.hdmi-stereo".  The leading
  # "~" makes WirePlumber treat the value as a regular expression.
  # Run `hdmi-audio-info` to see the real node names on this machine.
  hdmiNodePattern = "~alsa_output.*hdmi.*";
in
{
  # ── PipeWire / WirePlumber rules for HDMI outputs ──────────────────────────
  # Written to /etc/wireplumber/wireplumber.conf.d/51-hdmi-audio.conf.
  # These apply only to HDMI sinks — the analog output and its low-latency
  # JACK setup in common.nix are left untouched.
  services.pipewire.wireplumber.extraConfig."51-hdmi-audio" = {
    "monitor.alsa.rules" = [
      {
        matches = [ { "node.name" = hdmiNodePattern; } ];
        actions = {
          update-props = {
            # Never suspend the HDMI sink.  Resuming the codec is what makes
            # the start of a sound arrive late, and on many TVs it also drops
            # the HDMI audio link entirely for a moment.  The cost is a
            # permanently open device, which is irrelevant on a desktop.
            "session.suspend-timeout-seconds" = 0;

            # Pin an explicit, small ALSA period instead of letting PipeWire
            # negotiate one.  1024 samples × 2 periods ≈ 43 ms at 48 kHz —
            # low enough to be inaudible, high enough not to risk xruns on a
            # sink that is not being scheduled as tightly as a DAW output.
            "api.alsa.period-size" = 1024;
            "api.alsa.period-num" = 2;

            # Declare the TV's internal delay so players compensate for it.
            # WirePlumber adds this to the latency the node reports, and
            # anything honouring sink latency (mpv, VLC, browsers, Firefox,
            # Plasma's own playback) delays its video to match.
            "latency.internal.ns" = tvAudioDelayMs * 1000000;

            # If audio still stutters after the above, the device is probably
            # being driven in batch mode — uncomment to force PipeWire to
            # treat it as a normal interrupt-driven device:
            # "api.alsa.disable-batch" = true;
          };
        };
      }
    ];
  };

  # ── Keep the HDA controller awake ──────────────────────────────────────────
  # snd_hda_intel powers the codec down after ~1 s idle by default.  The GPU's
  # HDMI audio function is driven by the same module, and waking it costs
  # several hundred milliseconds — heard as a late or half-swallowed first
  # sound.  Disabling power save trades a fraction of a watt for that.
  boot.extraModprobeConfig = ''
    options snd_hda_intel power_save=0 power_save_controller=N
  '';

  # ── Diagnostics ────────────────────────────────────────────────────────────
  # `hdmi-audio-info` prints the HDMI sinks with their real node names, the
  # latency each one reports, and the current graph quantum — everything
  # needed to confirm the rules above actually took effect.
  environment.systemPackages = [
    (pkgs.writeShellScriptBin "hdmi-audio-info" ''
      set -u

      echo "── HDMI sinks ────────────────────────────────────────────────────"
      if ! ${pkgs.pulseaudio}/bin/pactl list sinks \
           | ${pkgs.gawk}/bin/awk 'BEGIN { RS = "\n\n"; found = 0 }
                                   /Name:.*hdmi/ { print; print ""; found = 1 }
                                   END { exit (found ? 0 : 1) }'; then
        echo "No HDMI sink found."
        echo "The TV must be connected and awake for one to appear, and the"
        echo "card profile must include HDMI output (check in pavucontrol,"
        echo "Configuration tab)."
      fi

      echo "── Graph clock ───────────────────────────────────────────────────"
      ${pkgs.pipewire}/bin/pw-metadata -n settings 2>/dev/null \
        | ${pkgs.gnugrep}/bin/grep -E "clock\.(rate|quantum)" \
        || echo "pw-metadata returned nothing — is PipeWire running?"

      echo
      echo "The 'Latency:' line above shows what the sink reports; the"
      echo "'configured' figure includes the tvAudioDelayMs compensation set"
      echo "in nixos-config/modules/hdmi-audio.nix. If a change there is not"
      echo "showing up, the node was not recreated — restart WirePlumber:"
      echo "  systemctl --user restart wireplumber"
    '')
  ];
}
