# JARVIS — handoff to a local session

You are picking up a voice-assistant stack that was written in a cloud container
with **no NixOS, no GPU, no audio device, and no `nix` binary**. Every Nix option
name was verified by reading nixpkgs source at the pinned revision, and the
Python compiles — but nothing has ever been built or run.

Your job is to make it actually work on the real machine. This file is the
briefing: what exists, what order to verify it in, and the specific things most
likely to be wrong.

**Do not treat any of this as known-good.** If something contradicts what you
observe on the machine, the machine is right.

---

## Ground rules

- Branch: `claude/home-manager-antigravity-9o9zo8`. Commit and push there.
  Never push to `main`.
- The repo lives at `/etc/nixos/nixos-config` on the target machine (the flake
  is `/etc/nixos/nixos-config#nixos`).
- `rebuild` is an alias for
  `sudo nixos-rebuild switch --flake /etc/nixos/nixos-config#nixos`.
- Prefer `sudo nixos-rebuild test --flake .#nixos` while iterating — it activates
  without adding a boot entry, so a bad generation is one reboot away from gone.

---

## What was added

```
JARVIS.md                                  user-facing docs (setup, tuning, troubleshooting)
nixos-config/modules/jarvis.nix            system: ollama-cuda, wyoming openwakeword/whisper/piper
nixos-config/home/modules/jarvis.nix       HM module: services.jarvis options + user systemd unit
nixos-config/scripts/jarvis/
    config.py                              JSON config loader (written by the HM module)
    audio.py                               mic capture, playback, VAD, RMS level
    wyoming_io.py                          Wyoming clients: wake word, STT, TTS
    tools.py                               tool schemas + implementations
    brain.py                               hybrid local/Claude router
    hud.py                                 websocket server for the Plasma widget
    main.py                                orchestrator state machine
    train-wakeword.sh                      custom wake-word training pipeline
nixos-config/dotfiles/plasmoids/jarvis-hud/   Plasma 6 applet (QML)
```

Wired into `hosts/nixos/default.nix` (system) and `home/radu.nix` (user).

Architecture in one line: four system daemons speak the Wyoming protocol; a
Python **user** service orchestrates them, executes tools, and pushes state to a
Plasma widget over a localhost websocket.

---

## Verification sequence

Work in this order. Each stage depends on the one above it, so a failure at
stage 3 is meaningless if stage 2 was never confirmed.

### 1. It evaluates

```bash
cd /etc/nixos/nixos-config
nix flake check 2>&1 | tail -40
# or, faster and more informative on errors:
sudo nixos-rebuild dry-build --flake .#nixos --show-trace 2>&1 | tail -60
```

Attribute-not-found errors here are the expected first failure. See the risk
register below — `qt6.qtwebsockets` and the `python3Packages` list are the
likely culprits.

### 2. It builds

```bash
sudo nixos-rebuild build --flake .#nixos
```

This downloads several GB (CUDA builds of Ollama and faster-whisper, plus
models). If a Python package fails to build rather than being missing, check
whether nixpkgs marked it broken at this pin.

### 3. The system daemons come up

```bash
sudo nixos-rebuild switch --flake .#nixos
systemctl status wyoming-openwakeword \
                 wyoming-faster-whisper-jarvis \
                 wyoming-piper-jarvis \
                 ollama
ss -ltnp | grep -E '104(00)|10300|10200|11434'
```

Expect four listeners. Piper downloads its voice model on first use, so its
first synthesis is slow — that is not a hang.

Confirm Ollama actually got the GPU:

```bash
journalctl -u ollama | grep -i -E 'cuda|gpu'
ollama list      # llama3.1:8b should be present
```

### 4. Audio hardware is visible to the daemon

This is the stage most likely to need real fixes, and it cannot be checked from
anywhere but the machine.

```bash
python3 -c "import sounddevice; print(sounddevice.query_devices())"
```

If that import fails with a PortAudio library error, see risk #3. If it works
but the default input is wrong, set `services.jarvis.inputDevice` to the exact
device name and rebuild.

Prove capture and playback independently of everything else:

```bash
# record 3s, play it back
python3 - <<'EOF'
import sounddevice as sd, numpy as np
a = sd.rec(int(3*16000), samplerate=16000, channels=1, dtype='int16'); sd.wait()
print("peak", np.abs(a).max())      # should be well above ~500 if the mic works
sd.play(a, 16000); sd.wait()
EOF
```

### 5. The Wyoming round-trip works

Before debugging the daemon, prove each service answers. This is the highest-risk
code in the repo (see risk #1), so test it in isolation:

```bash
# TTS: should produce audible speech and a non-zero byte count
python3 - <<'EOF'
import asyncio, sys
sys.path.insert(0, "/etc/nixos/nixos-config/scripts")
from jarvis.wyoming_io import synthesize
from jarvis.config import WyomingEndpoint
pcm, rate = asyncio.run(synthesize(WyomingEndpoint("127.0.0.1", 10200), "Systems nominal.", "en_GB-alan-medium"))
print(len(pcm), "bytes at", rate, "Hz")
EOF
```

Do the same for `transcribe()` with a recorded utterance. If the wyoming API
signatures are wrong, they will fail here with a `TypeError` or `AttributeError`
and the fix is local to `wyoming_io.py`.

### 6. The daemon runs

```bash
systemctl --user status jarvis
journalctl --user -u jarvis -f
```

Expect `JARVIS ready — say the wake word`. Then say "Hey Jarvis", wait for the
chime, and speak. The log traces every stage: detection → transcript → tool
calls → reply.

If it never wakes, dump the wake service's own log — openWakeWord logs
confidence scores, which tells you whether to adjust
`services.wyoming.openwakeword.threshold` or whether audio is not reaching it at
all.

### 7. Brains and tools

Test in this order, because each isolates a different layer:

1. `"Hey Jarvis, what's the GPU at?"` — local model + a read-only tool.
2. `"Hey Jarvis, open Firefox"` — local model + a side-effecting tool.
3. `"Hey Jarvis, explain what a Nix flake actually does"` — forces escalation to
   Claude (matches `escalateHints`). Needs `~/.config/jarvis/anthropic-key`.
4. `"Hey Jarvis, how many files are in my downloads folder?"` — exercises the
   shell path and the spoken-confirmation gate. **Verify the confirmation
   actually blocks**: say "no" and confirm nothing ran.

### 8. The HUD

Add the widget (*Add Widgets…* → **JARVIS HUD**). If it does not appear in the
list, the QML module is missing — see risk #2. `plasmashell --replace &` or a
re-login is needed after the rebuild that adds it.

---

## Risk register

Ranked by how likely I think they are to bite. Each has a concrete fix.

### 1. Wyoming library API drift — **most likely code failure**

`scripts/jarvis/wyoming_io.py` calls `python3Packages.wyoming` from memory of the
protocol library, not from reading the installed version. Specifically unverified:

- `AsyncTcpClient(host, port)` positional constructor and its async context
  manager, plus `.connect()` / `.disconnect()`
- `Detect(names=[...])`
- `AudioChunk(rate=, width=, channels=, audio=)`
- `Synthesize(text=)` with `.voice = SynthesizeVoice(name=)` assigned after
  construction
- `AudioStart.from_event(event).rate`

Check the installed source directly rather than guessing:

```bash
python3 -c "import wyoming, os; print(os.path.dirname(wyoming.__file__))"
# then read client.py, audio.py, asr.py, tts.py, wake.py in that directory
```

Fix whatever does not match. The event *semantics* are right; only the
constructor spellings are in doubt.

### 2. `qt6.qtwebsockets` attribute / QML import path

`modules/jarvis.nix` adds `qt6.qtwebsockets` to `environment.systemPackages` so
`import QtWebSockets` resolves in the applet. Two ways this fails:

- The attribute does not exist under that name → evaluation error at stage 1.
  Find the right one: `nix search nixpkgs qtwebsockets`, or check
  `kdePackages.qtwebsockets`.
- It exists but plasmashell still cannot find the QML module. Confirm with
  `ls /run/current-system/sw/lib/qt-6/qml/QtWebSockets`. If the path differs,
  the applet's `import QtWebSockets` line is the thing to work around.

Evidence it should work: the existing `luisbocanegra.audio.visualizer` widget
already uses a websocket transport on this machine, so something is providing it.
Find out what and match it.

### 3. `sounddevice` cannot find PortAudio

Classic NixOS failure — the Python wrapper loads `libportaudio.so` by name.
nixpkgs usually patches this, but if `import sounddevice` raises `OSError`, the
fix is to add `pkgs.portaudio` to the wrapper's library path in
`home/modules/jarvis.nix`:

```nix
jarvis = pkgs.writeShellScriptBin "jarvis" ''
  export LD_LIBRARY_PATH=${pkgs.portaudio}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
  export PYTHONPATH=${../../scripts}''${PYTHONPATH:+:$PYTHONPATH}
  exec ${pythonEnv}/bin/python -m jarvis "$@"
'';
```

### 4. Anthropic SDK is older than the parameters used

`brain.py` passes `betas=["server-side-fallback-2026-07-01"]`, `fallbacks="default"`,
and `output_config={"effort": ...}` to `client.beta.messages.create`. If the
`anthropic` package at this nixpkgs pin predates them, expect a `TypeError` on
an unexpected keyword argument, or a 400 from the API.

Check the installed version first:

```bash
python3 -c "import anthropic; print(anthropic.__version__)"
```

Minimal fallback — drop the newer parameters, keep the model:

```python
response = await asyncio.to_thread(
    client.messages.create,          # note: not client.beta
    model=self.cfg.brain.claude_model,
    max_tokens=self.cfg.brain.claude_max_tokens,
    system=self.system,
    tools=tools,
    messages=messages,
)
```

Losing `fallbacks` only means a refused request returns the refusal instead of
being retried — the `stop_reason == "refusal"` branch already handles that
gracefully. Do **not** "fix" this by setting `thinking: {"type": "disabled"}`:
on Opus 5 that can make tool calls arrive as plain text that silently never
execute, which is exactly the wrong failure mode here.

### 5. `webrtcvad` package name

nixpkgs has carried both `webrtcvad` and `webrtcvad-wheels` at different times,
and one has been marked broken before. If the Python env fails to build, try
swapping the name in `home/modules/jarvis.nix`. If neither works, `audio.py`'s
`SilenceDetector` can fall back to a plain RMS threshold — worse, but not
blocking.

### 6. Ollama tool calling on `llama3.1:8b`

`brain.py` reads `response.get("message")` and `message.get("tool_calls")`.
Recent `ollama-python` returns pydantic `ChatResponse` objects that are still
subscriptable, so this *should* work — but verify with one call rather than
assuming.

Separately: 8B models are mediocre at tool selection. If it chats instead of
acting, that is a model-quality problem, not a bug. Try `qwen2.5:14b` (fits in
8 GB at 4-bit, noticeably better at tools) by changing both
`services.ollama.loadModels` and `services.jarvis.brain.localModel`.

### 7. openWakeWord `--preload-model` flag

`modules/jarvis.nix` passes `extraArgs = [ "--preload-model" "hey_jarvis" ]`.
If the service fails to start with an argparse error, check the real flag:

```bash
nix run nixpkgs#wyoming-openwakeword -- --help
```

Dropping the flag entirely is a safe fallback — it just loads every bundled
model instead of one.

### 8. HM option default referencing `config.home.homeDirectory`

`brain.apiKeyFile` defaults to `"${config.home.homeDirectory}/.config/jarvis/anthropic-key"`.
This should be fine, but if evaluation hits infinite recursion, hardcode
`/home/radu/.config/jarvis/anthropic-key` and move on.

### 9. Self-triggering

The daemon drains the mic queue after speaking, but a loud speaker near an open
mic can still wake it mid-reply. If you see a turn start immediately after every
reply, that is what is happening — the honest fix is to stop feeding the wake
service while `speaking`, which `main.py` already does structurally; verify the
drain is sufficient before adding anything cleverer.

---

## Things I could not check at all

- Whether the whole pipeline's latency is tolerable end to end. Measure it.
  Wake→chime should be well under a second; chime→reply depends on the model.
- Whether `en_GB-alan-medium` is a voice you actually want to listen to.
  Samples: https://rhasspy.github.io/piper-samples/
- Whether `base-int8` whisper is accurate enough for your vocabulary. If it
  mangles technical words, try `small-int8` or extend `initialPrompt`.
- Whether the HUD looks good. The QML is written blind — the reactor ring,
  spacing, and colours have never been rendered. Expect to iterate on
  `dotfiles/plasmoids/jarvis-hud/contents/ui/main.qml`. Fast loop for widget
  work: `plasmoidviewer -a ~/.local/share/plasma/plasmoids/org.jarvis.hud`
  (from `kdePackages.plasma-sdk`) instead of a full rebuild each time.
- `train-wakeword.sh` end to end. Its `python -m openwakeword.train` invocation
  is the least certain part — upstream's canonical path is the notebook at
  `openwakeword/notebooks/automatic_model_training.ipynb`, and the script says so
  in its error message. Only relevant if a custom wake word is wanted; the
  pretrained `hey_jarvis` needs none of it.

---

## Useful while iterating

```bash
# Restart the daemon after editing a .py file (no rebuild needed —
# PYTHONPATH points at the repo, but the wrapper is a store path, so:)
sudo nixos-rebuild test --flake /etc/nixos/nixos-config#nixos \
  && systemctl --user restart jarvis

# Run the daemon in the foreground instead, for a tight edit loop:
systemctl --user stop jarvis
PYTHONPATH=/etc/nixos/nixos-config/scripts python3 -m jarvis

# Watch state without the widget
websocat ws://127.0.0.1:8770        # websocat is already in modules/development.nix

# Audit what the shell tool has executed
journalctl --user -u jarvis -p warning
```

---

## When you are done

Commit to `claude/home-manager-antigravity-9o9zo8` with a message that says what
you actually verified on hardware versus what is still untested — the previous
commit was explicit that nothing was tested, and the next one should be equally
explicit about what changed. Update `JARVIS.md` if the setup steps turned out to
be wrong, and delete the risk-register entries here that you have resolved so
this file stays honest about what is still unknown.
