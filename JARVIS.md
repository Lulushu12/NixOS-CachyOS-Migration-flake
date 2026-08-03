# JARVIS — local voice assistant

A wake-word voice assistant that runs on this machine: it hears you, transcribes
locally, reasons with a local model or Claude, speaks back, and can actually
drive the desktop.

Nothing is sent anywhere unless a request escalates to Claude — and even then
only the *transcript* leaves, never the audio.

---

## What it is made of

| Layer | Component | Where |
|---|---|---|
| Wake word | openWakeWord (`:10400`) | `modules/jarvis.nix` |
| Speech → text | faster-whisper, CUDA (`:10300`) | `modules/jarvis.nix` |
| Text → speech | Piper (`:10200`) | `modules/jarvis.nix` |
| Local reasoning | Ollama, CUDA (`:11434`) | `modules/jarvis.nix` |
| Orchestrator | Python daemon, systemd **user** service | `home/modules/jarvis.nix` |
| Visual HUD | Plasma 6 applet | `dotfiles/plasmoids/jarvis-hud/` |

The first four are system daemons. The orchestrator runs as *you* because it
needs your Wayland and DBus session to control KDE, and because it reads your
Anthropic API key — which must never end up in the Nix store.

The speech services talk the Wyoming protocol (Home Assistant's voice-pipeline
protocol), so each one is independently swappable.

---

## First run

```bash
rebuild
```

This is a large first build: the CUDA builds of Ollama and faster-whisper, plus
model downloads. Budget several gigabytes and a long coffee.

Then set up the Claude half (skip if you want it fully offline — see
[Going fully local](#going-fully-local)):

```bash
mkdir -p ~/.config/jarvis
printf 'sk-ant-...' > ~/.config/jarvis/anthropic-key
chmod 600 ~/.config/jarvis/anthropic-key
systemctl --user restart jarvis
```

Check it came up:

```bash
systemctl --user status jarvis
journalctl --user -u jarvis -f
```

You should see `JARVIS ready — say the wake word`. Say **"Hey Jarvis"**, wait for
the chime, then talk.

Finally, add the HUD: right-click the desktop or panel → *Add Widgets…* →
**JARVIS HUD**.

---

## Talking to it

| You say | What happens |
|---|---|
| "Hey Jarvis, open Firefox" | `launch_app` |
| "…pause the music" / "what's playing?" | `media_control` via MPRIS |
| "…turn it down a bit" | `pamixer` |
| "…switch to desktop three" | KWin over DBus |
| "…how's the GPU doing?" | temperature, VRAM, load |
| "…what generation am I on?" | `nixos-rebuild list-generations` |
| "…rebuild the system" | opens a terminal so you type your own password |
| "…how many files are in my downloads folder?" | shell command, read back for confirmation first |
| "…explain what a Nix flake actually does" | escalates to Claude |

---

## The hybrid brain

Three modes, set by `services.jarvis.brain.mode`:

- **`local`** — Ollama only. Fully offline, no API key, nothing leaves the box.
- **`claude`** — everything goes to the Anthropic API.
- **`hybrid`** (default) — routed:

  1. Long requests (>25 words) or ones matching `escalateHints`
     ("explain", "why", "compare", "write", "draft", "research"…) go **straight
     to Claude**. Trying an 8B model first on those only adds a pause before the
     escalation.
  2. Everything else runs **locally**. The local model has the same tool set plus
     an `escalate` tool it can call when it judges a request beyond it.
  3. Any local failure — crash, empty answer, malformed tool call — falls through
     to Claude rather than surfacing an error.

Both brains get the same system prompt and the same tools, so which one answered
should only be visible in latency and quality.

Claude runs at `effort = "low"` by default to keep the pause conversational.
Raise it in `home/modules/jarvis.nix` if you'd rather it thought harder:

```nix
services.jarvis.brain.claudeEffort = "medium";
```

---

## Customising it

Everything is a Nix option in `home/modules/jarvis.nix`. The interesting ones:

```nix
services.jarvis = {
  assistantName = "JARVIS";       # what it calls itself
  userName      = "Radu";         # what it calls you
  personality   = ''
    Be dry, precise, and unhurried. Skip pleasantries and filler.
  '';                             # tone, humour, standing preferences

  voice    = "en_GB-alan-medium"; # https://rhasspy.github.io/piper-samples/
  wakeWord = "hey_jarvis";

  silenceSeconds = 1.2;           # how long a pause ends your sentence
};
```

`personality` is free text appended to the system prompt — that is the whole
knob. Rebuild and the daemon restarts with the new character.

Changing the **voice** means changing it in two places, since the Piper server
loads the model and the client requests it by name:

```nix
# modules/jarvis.nix
services.wyoming.piper.servers.jarvis.voice = "en_GB-northern_english_male-medium";
# home/modules/jarvis.nix
services.jarvis.voice = "en_GB-northern_english_male-medium";
```

### Changing the wake word

The wake word is a *trained audio model*, not a string — this is the one part of
personalisation that costs real effort.

Pretrained and free: `hey_jarvis`, `alexa`, `hey_mycroft`, `hey_rhasspy`,
`ok_nabu`.

For anything else, train one:

```bash
./nixos-config/scripts/jarvis/train-wakeword.sh "hey friday"
```

Piper generates ~30,000 synthetic spoken variants of the phrase plus adversarial
near-misses, and a small classifier is trained on a frozen speech-embedding
model. No recordings of your voice are needed. Expect 45–90 minutes on the 2070
SUPER. The script installs the result to `/var/lib/jarvis/wakewords/` and prints
the two lines you need to change.

---

## Shell execution

The assistant can compose and run arbitrary shell commands. This is the most
powerful capability and the one worth being deliberate about — the real risk is
not malice but **mishearing**.

Two guards, both on by default:

1. **Spoken confirmation.** The command is read back to you and nothing runs
   until you say yes. A transcription error has to survive being spoken aloud.
2. **A refuse list.** `rm -rf /`, `mkfs`, `dd` to a block device, `shred`, and
   fork bombs are rejected outright, confirmation or not.

The refuse list is not a security boundary — anyone at this keyboard can run
those anyway. It exists so speech recognition errors cannot be catastrophic.

To drop the confirmation prompt (not recommended):

```nix
services.jarvis.capabilities.shell.requireConfirmation = false;
```

To turn shell execution off entirely:

```nix
services.jarvis.capabilities.shell.enable = false;
```

Every executed command is logged at WARNING level — `journalctl --user -u jarvis
-p warning` is the audit trail.

---

## Going fully local

```nix
services.jarvis.brain.mode = "local";
```

No API key needed, no network. The tradeoff is real: an 8B model handles
"open Firefox" and "what's the GPU at" fine, but is noticeably weaker at
multi-step reasoning and at picking the right tool for an oddly-phrased request.

A larger local model helps if you have the VRAM headroom — `qwen2.5:14b` is the
practical ceiling on 8 GB at 4-bit:

```nix
# modules/jarvis.nix
services.ollama.loadModels = [ "qwen2.5:14b" ];
# home/modules/jarvis.nix
services.jarvis.brain.localModel = "qwen2.5:14b";
```

Whatever you pick must support tool calling, or the assistant can talk but not
act.

---

## Tuning

**It triggers when you didn't say the wake word** — raise the threshold:

```nix
services.wyoming.openwakeword.threshold = 0.7;  # default 0.5
```

**It ignores you** — lower it toward 0.3, and check the mic is the default input
in System Settings.

**It cuts you off mid-sentence** — raise `services.jarvis.silenceSeconds`.

**It mishears technical words** — either move to a bigger whisper model:

```nix
services.wyoming.faster-whisper.servers.jarvis.model = "small-int8";
```

or bias the decoder, which is cheaper and often enough:

```nix
services.wyoming.faster-whisper.servers.jarvis.initialPrompt =
  "NixOS, Plasma, KDE, flake, nixpkgs, systemd, Kubernetes, PostgreSQL.";
```

---

## Troubleshooting

```bash
# Is the whole stack up?
systemctl status wyoming-openwakeword wyoming-faster-whisper-jarvis \
                 wyoming-piper-jarvis ollama
systemctl --user status jarvis

# Follow the conversation live
journalctl --user -u jarvis -f
```

**No microphone** — list what PortAudio can see, then pin it explicitly:

```bash
python3 -c "import sounddevice; print(sounddevice.query_devices())"
```

```nix
services.jarvis.inputDevice = "alsa_input.usb-Blue_Microphones";
```

**HUD widget shows "Assistant not running"** — the daemon is down or the
WebSocket port is wrong. Check `systemctl --user status jarvis`. If the widget
fails to appear at all in *Add Widgets*, the QML WebSocket module is missing;
`qt6.qtwebsockets` is in `modules/jarvis.nix` for exactly this reason and needs a
rebuild plus a `plasmashell --replace &` or a re-login.

**It wakes itself up** — its own voice is being picked up by the mic. Move the
mic, or lower the output volume; the daemon already discards captured audio after
speaking, but a loud speaker close to an open mic can still bleed through.

**Ollama is slow / on CPU** — confirm CUDA:

```bash
journalctl -u ollama | grep -i cuda
nvidia-smi   # should show ollama holding VRAM while it answers
```

---

## Turning it off

Comment both imports out and rebuild:

```nix
# hosts/nixos/default.nix
# ../../modules/jarvis.nix

# home/radu.nix
# ./modules/jarvis.nix
```

Or keep it installed but idle:

```bash
systemctl --user stop jarvis
```
