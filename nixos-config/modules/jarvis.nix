# JARVIS — system-level voice assistant stack.
#
# ─── What lives here ─────────────────────────────────────────────────────────
# The three speech services and the local LLM, all as system daemons:
#
#   openWakeWord    :10400  — listens for the wake phrase
#   faster-whisper  :10300  — speech to text (CUDA on the 2070 SUPER)
#   Piper           :10200  — text to speech
#   Ollama          :11434  — local reasoning model
#
# They speak the Wyoming protocol (Home Assistant's voice-pipeline protocol).
# The orchestrator that ties them together is a *user* service — see
# home/modules/jarvis.nix — because it needs the Wayland and DBus session to
# drive KDE, and it holds the user's Anthropic API key.
#
# ─── First rebuild ───────────────────────────────────────────────────────────
# This pulls the CUDA build of Ollama plus the whisper and Piper models, so the
# first `rebuild` after enabling it downloads several gigabytes. Afterwards,
# `ollama pull` for a different model is the only manual step you might want.
#
# ─── Turning it off ──────────────────────────────────────────────────────────
# Comment the import out of hosts/nixos/default.nix. The user service degrades
# to logging connection errors; comment out its import too for a clean stop.

{ pkgs, ... }:

{
  # ── Local LLM ──────────────────────────────────────────────────────────────
  # ollama-cuda rather than plain ollama: the RTX 2070 SUPER's 8 GB comfortably
  # holds an 8B model at 4-bit quantisation, and GPU inference is the difference
  # between a conversational reply and an awkward pause.
  services.ollama = {
    enable  = true;
    package = pkgs.ollama-cuda;
    host    = "127.0.0.1";
    port    = 11434;

    # Pulled automatically on activation. Swap for a different model here and
    # update brain.localModel in home/modules/jarvis.nix to match.
    loadModels = [ "llama3.1:8b" ];
  };

  # ── Wake word detection ────────────────────────────────────────────────────
  # openWakeWord ships pretrained models including "hey_jarvis", so the default
  # wake phrase works with no training. --preload-model keeps only that one in
  # memory; drop the flag to have every bundled model listening at once.
  #
  # customModelsDirectories points at a world-readable path on purpose: the
  # service runs under DynamicUser with ProtectHome=true, so a model trained
  # into ~/ would be invisible to it. scripts/jarvis/train-wakeword.sh installs
  # there.
  services.wyoming.openwakeword = {
    enable = true;
    uri    = "tcp://127.0.0.1:10400";

    # Raise toward 1.0 if it triggers on the TV; lower toward 0.0 if it ignores
    # you. 0.5 is openWakeWord's default and a sane starting point.
    threshold         = 0.5;
    triggerLevel      = 1;
    # Ignore repeat detections for this long after a wake, so one utterance of
    # the wake phrase cannot start two overlapping turns.
    refractorySeconds = 2;

    customModelsDirectories = [ "/var/lib/jarvis/wakewords" ];
    extraArgs = [ "--preload-model" "hey_jarvis" ];
  };

  # ── Speech to text ─────────────────────────────────────────────────────────
  # base-int8 transcribes a short command in well under a second on this GPU.
  # Move to "small-int8" or "medium-int8" if it mishears technical vocabulary;
  # both are noticeably slower but markedly more accurate on proper nouns.
  services.wyoming.faster-whisper.servers.jarvis = {
    enable   = true;
    uri      = "tcp://127.0.0.1:10300";
    model    = "base-int8";
    language = "en";
    device   = "cuda";

    # Biases the decoder toward vocabulary it would otherwise mangle. Worth
    # extending with the names of apps and projects you talk about.
    initialPrompt = "NixOS, Plasma, KDE, flake, nixpkgs, systemd, Claude, Antigravity.";
  };

  # ── Text to speech ─────────────────────────────────────────────────────────
  # Voice samples: https://rhasspy.github.io/piper-samples/
  # The model is fetched on first use and cached under the service's state dir.
  services.wyoming.piper.servers.jarvis = {
    enable  = true;
    uri     = "tcp://127.0.0.1:10200";
    voice   = "en_GB-alan-medium";
    useCUDA = false;  # Piper is fast enough on CPU; leaves the GPU for whisper + Ollama
  };

  # ── State directory for custom wake-word models ───────────────────────────
  systemd.tmpfiles.rules = [
    "d /var/lib/jarvis          0755 root root -"
    "d /var/lib/jarvis/wakewords 0755 root root -"
  ];

  # ── Runtime dependencies of the tool layer ────────────────────────────────
  # The orchestrator shells out to these. They are listed explicitly in the user
  # unit's PATH too, but having them system-wide makes manual debugging easier.
  environment.systemPackages = with pkgs; [
    playerctl   # MPRIS media control (play/pause/skip)
    glib        # gdbus — drives KWin over the session bus
    pamixer     # scriptable volume control
    ollama-cuda # `ollama pull`, `ollama list` from a terminal

    # QML WebSocket module for the HUD widget. It has to be system-wide rather
    # than in the user profile: plasmashell searches
    # /run/current-system/sw/lib/qt-6/qml, not ~/.nix-profile. Without it the
    # widget fails to load with "module QtWebSockets is not installed".
    qt6.qtwebsockets
  ];
}
