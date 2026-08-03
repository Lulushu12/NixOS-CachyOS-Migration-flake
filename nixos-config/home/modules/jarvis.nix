# JARVIS — user-level configuration for the voice assistant.
#
# The speech services and the local model are system daemons (modules/jarvis.nix).
# This module owns the orchestrator that drives them, and it runs as a *user*
# service for two reasons: it needs the Wayland/DBus session to control KDE, and
# it reads an Anthropic API key that must never enter the Nix store.
#
# ─── Personalisation ─────────────────────────────────────────────────────────
# Everything the assistant knows about you is an option below. Change a value,
# rebuild, and the daemon restarts with the new config — nothing is hand-edited
# at runtime.
#
# ─── The API key ─────────────────────────────────────────────────────────────
# brain.mode = "hybrid" (the default) needs an Anthropic key. Put it in the file
# named by brain.apiKeyFile — it is read at runtime, never copied into the store:
#
#     mkdir -p ~/.config/jarvis
#     printf 'sk-ant-...' > ~/.config/jarvis/anthropic-key
#     chmod 600 ~/.config/jarvis/anthropic-key
#
# With no key present the assistant silently runs local-only: every escalation
# falls back to the Ollama model instead of erroring.

{ config, lib, pkgs, ... }:

let
  cfg = config.services.jarvis;

  # Runtime interpreter. sounddevice reaches PortAudio (and through it PipeWire);
  # wyoming speaks the protocol the three speech services use.
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    numpy        # PCM framing and the RMS level fed to the HUD
    sounddevice  # microphone capture and playback via PortAudio
    webrtcvad    # end-of-utterance detection
    wyoming      # Wyoming protocol client (wake word, STT, TTS)
    websockets   # HUD transport — same pattern as the audio-visualizer widget
    anthropic    # Claude, for the escalation half of hybrid mode
    ollama       # local model client
  ]);

  # The daemon source lives in the repo rather than as a derivation of its own,
  # so editing a .py file and rebuilding is a one-step loop.
  jarvis = pkgs.writeShellScriptBin "jarvis" ''
    export PYTHONPATH=${../../scripts}''${PYTHONPATH:+:$PYTHONPATH}
    exec ${pythonEnv}/bin/python -m jarvis "$@"
  '';

  configFile = {
    assistant_name = cfg.assistantName;
    user_name      = cfg.userName;
    personality    = cfg.personality;

    wake_word = cfg.wakeWord;
    wake_uri  = cfg.wakeUri;
    asr_uri   = cfg.asrUri;
    tts_uri   = cfg.ttsUri;
    tts_voice = cfg.voice;

    input_device  = cfg.inputDevice;
    output_device = cfg.outputDevice;

    silence_seconds       = cfg.silenceSeconds;
    max_utterance_seconds = cfg.maxUtteranceSeconds;

    hud_enabled = cfg.hud.enable;
    hud_port    = cfg.hud.port;

    brain = {
      mode                = cfg.brain.mode;
      ollama_host         = cfg.brain.ollamaHost;
      local_model         = cfg.brain.localModel;
      claude_model        = cfg.brain.claudeModel;
      claude_max_tokens   = cfg.brain.claudeMaxTokens;
      claude_effort       = cfg.brain.claudeEffort;
      api_key_file        = cfg.brain.apiKeyFile;
      escalate_hints      = cfg.brain.escalateHints;
      escalate_word_count = cfg.brain.escalateWordCount;
    };

    capabilities = {
      conversation = true;
      desktop      = cfg.capabilities.desktop;
      system       = cfg.capabilities.system;
      nixos        = cfg.capabilities.nixos;
      shell = {
        enabled              = cfg.capabilities.shell.enable;
        require_confirmation = cfg.capabilities.shell.requireConfirmation;
        deny_patterns        = cfg.capabilities.shell.denyPatterns;
        timeout_seconds      = cfg.capabilities.shell.timeoutSeconds;
      };
    };
  };
in
{
  options.services.jarvis = {
    enable = lib.mkEnableOption "the JARVIS voice assistant orchestrator";

    assistantName = lib.mkOption {
      type = lib.types.str;
      default = "JARVIS";
      description = ''
        What the assistant calls itself in conversation. Purely cosmetic — it
        does not change the wake word, which is a trained audio model (see
        {option}`services.jarvis.wakeWord`).
      '';
    };

    userName = lib.mkOption {
      type = lib.types.str;
      default = "Radu";
      description = "What the assistant calls you.";
    };

    personality = lib.mkOption {
      type = lib.types.lines;
      default = "";
      example = "Be dry and understated. Never gush. A little sardonic is fine.";
      description = ''
        Free text appended to the system prompt. This is where tone, humour,
        catchphrases, and standing preferences go.
      '';
    };

    wakeWord = lib.mkOption {
      type = lib.types.str;
      default = "hey_jarvis";
      description = ''
        openWakeWord model name. The pretrained set is `hey_jarvis`,
        `alexa`, `hey_mycroft`, `hey_rhasspy`, and `ok_nabu`.

        For a custom phrase, train a model with
        `scripts/jarvis/train-wakeword.sh` and set this to its name.
      '';
    };

    voice = lib.mkOption {
      type = lib.types.str;
      default = "en_GB-alan-medium";
      description = ''
        Piper voice model. Samples: https://rhasspy.github.io/piper-samples/
        Must match {option}`services.wyoming.piper.servers.jarvis.voice`.
      '';
    };

    wakeUri = lib.mkOption {
      type = lib.types.str;
      default = "tcp://127.0.0.1:10400";
      description = "openWakeWord endpoint.";
    };

    asrUri = lib.mkOption {
      type = lib.types.str;
      default = "tcp://127.0.0.1:10300";
      description = "faster-whisper endpoint.";
    };

    ttsUri = lib.mkOption {
      type = lib.types.str;
      default = "tcp://127.0.0.1:10200";
      description = "Piper endpoint.";
    };

    inputDevice = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      example = "alsa_input.usb-Blue_Microphones";
      description = ''
        PortAudio input device name. `null` uses the system default.
        List candidates with:
        `python3 -c "import sounddevice; print(sounddevice.query_devices())"`
      '';
    };

    outputDevice = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "PortAudio output device name; `null` uses the default.";
    };

    silenceSeconds = lib.mkOption {
      type = lib.types.float;
      default = 1.2;
      description = ''
        How long you have to stop talking before the assistant decides your
        sentence is finished. Lower feels snappier but clips people who pause
        mid-thought.
      '';
    };

    maxUtteranceSeconds = lib.mkOption {
      type = lib.types.float;
      default = 20.0;
      description = "Hard ceiling on one utterance, so a stuck mic cannot record forever.";
    };

    hud = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = ''
          Serve assistant state over a local WebSocket for the Plasma HUD widget.
          Harmless to leave on with no widget added — nothing connects.
        '';
      };

      port = lib.mkOption {
        type = lib.types.port;
        default = 8770;
        description = "Localhost-only WebSocket port for the HUD widget.";
      };
    };

    brain = {
      mode = lib.mkOption {
        type = lib.types.enum [ "local" "claude" "hybrid" ];
        default = "hybrid";
        description = ''
          - `local`: Ollama only. Fully offline, nothing leaves the machine.
          - `claude`: every request goes to the Anthropic API.
          - `hybrid`: the local model handles commands and small talk; anything
            long, or that it flags as beyond it, escalates to Claude.
        '';
      };

      ollamaHost = lib.mkOption {
        type = lib.types.str;
        default = "http://127.0.0.1:11434";
        description = "Ollama API endpoint.";
      };

      localModel = lib.mkOption {
        type = lib.types.str;
        default = "llama3.1:8b";
        description = ''
          Ollama model tag. Must be pulled — add it to
          {option}`services.ollama.loadModels` in modules/jarvis.nix, or run
          `ollama pull` yourself. Pick a model with tool-calling support;
          without it the assistant can talk but cannot act.
        '';
      };

      claudeModel = lib.mkOption {
        type = lib.types.str;
        default = "claude-opus-5";
        description = "Anthropic model used for escalated requests.";
      };

      claudeMaxTokens = lib.mkOption {
        type = lib.types.int;
        default = 4096;
        description = ''
          Output ceiling per request. Spoken replies are short, but the tool
          loop needs headroom, so this is well above what a sentence costs.
        '';
      };

      claudeEffort = lib.mkOption {
        type = lib.types.enum [ "low" "medium" "high" "xhigh" "max" ];
        default = "low";
        description = ''
          How hard Claude thinks before answering. `low` keeps the pause
          conversational; raise it if escalated questions deserve more care and
          you can live with waiting a few seconds longer.
        '';
      };

      apiKeyFile = lib.mkOption {
        type = lib.types.nullOr lib.types.str;
        default = "${config.home.homeDirectory}/.config/jarvis/anthropic-key";
        description = ''
          Path to a file holding the Anthropic API key — either the bare key or
          an `ANTHROPIC_API_KEY=...` line. Read at runtime and never copied into
          the Nix store. If the file is missing, the assistant runs local-only.
        '';
      };

      escalateHints = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ "explain" "why" "compare" "write" "draft" "summarise" "summarize" "research" ];
        description = ''
          Case-insensitive substrings that route a request straight to Claude,
          skipping the local model. These are the request shapes an 8B model
          reliably does worse at, so trying locally first only adds latency.
        '';
      };

      escalateWordCount = lib.mkOption {
        type = lib.types.int;
        default = 25;
        description = "Anything longer than this many words goes straight to Claude.";
      };
    };

    capabilities = {
      desktop = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Launch apps, control media and volume, switch virtual desktops.";
      };

      system = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Read CPU load, memory, disk space, and GPU temperature.";
      };

      nixos = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = ''
          Query generations, and open a terminal for rebuild / rollback /
          garbage-collect. The mutating actions always run in a visible terminal
          so you enter your own password and watch the output.
        '';
      };

      shell = {
        enable = lib.mkOption {
          type = lib.types.bool;
          default = true;
          description = ''
            Let the assistant compose and run arbitrary shell commands.

            This is the most powerful capability and the one worth thinking
            about: a misheard word becomes a real command. Leave
            {option}`requireConfirmation` on unless you have a specific reason
            not to.
          '';
        };

        requireConfirmation = lib.mkOption {
          type = lib.types.bool;
          default = true;
          description = ''
            Speak the command back and wait for a spoken "yes" before running
            it. This is what stops a transcription error from executing.
          '';
        };

        denyPatterns = lib.mkOption {
          type = lib.types.listOf lib.types.str;
          default = [ ];
          description = ''
            Regexes refused outright, confirmation or not. Empty means "use the
            built-in list", which covers `rm -rf /`, `mkfs`, `dd` to a block
            device, `shred`, and fork bombs.

            Not a security boundary — anyone at this keyboard can run these
            anyway. It exists so speech recognition errors cannot be
            catastrophic.
          '';
        };

        timeoutSeconds = lib.mkOption {
          type = lib.types.int;
          default = 60;
          description = "Kill a command that runs longer than this.";
        };
      };
    };
  };

  config = lib.mkIf cfg.enable {
    home.packages = [ jarvis ];

    xdg.configFile."jarvis/config.json".text = builtins.toJSON configFile;

    # The Plasma HUD widget. After the first rebuild, add it from
    # "Add Widgets…" — it appears as "JARVIS HUD".
    home.file.".local/share/plasma/plasmoids/org.jarvis.hud" = {
      source    = ../../dotfiles/plasmoids/jarvis-hud;
      recursive = true;
    };

    systemd.user.services.jarvis = {
      Unit = {
        Description = "${cfg.assistantName} voice assistant";
        # Needs the graphical session for DBus and the Wayland socket, and
        # PipeWire for the microphone.
        After  = [ "graphical-session.target" "pipewire.service" ];
        PartOf = [ "graphical-session.target" ];
      };

      Service = {
        ExecStart = "${jarvis}/bin/jarvis";
        Restart   = "on-failure";
        RestartSec = 5;
        # The speech services and Ollama may still be warming up at login.
        # Restarting on failure covers it, but a short delay avoids noisy logs.
        ExecStartPre = "${pkgs.coreutils}/bin/sleep 3";
        # Explicit PATH for the tool layer, so shelling out does not depend on
        # whatever the session happens to have inherited.
        Environment = [
          "PATH=${lib.makeBinPath (with pkgs; [
            playerctl pamixer glib coreutils kitty nixos-rebuild
          ])}:/run/current-system/sw/bin:%h/.nix-profile/bin"
          "PYTHONUNBUFFERED=1"
        ];
      };

      Install.WantedBy = [ "graphical-session.target" ];
    };
  };
}
