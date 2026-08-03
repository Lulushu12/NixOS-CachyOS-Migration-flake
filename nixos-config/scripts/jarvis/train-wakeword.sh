#!/usr/bin/env bash
#
# Train a custom openWakeWord model for an arbitrary wake phrase.
#
# The pretrained "hey_jarvis" model works out of the box, so this is only needed
# if you want the assistant to answer to something else. openWakeWord models are
# trained entirely on synthetic speech: Piper generates tens of thousands of
# spoken variants of your phrase, plus adversarial near-misses, and a small
# classifier is trained on top of a frozen speech-embedding model. That is why
# this needs no recordings of your own voice.
#
# Expect 45-90 minutes on the RTX 2070 SUPER, most of it in generation.
#
#   ./train-wakeword.sh "hey friday"
#
# When it finishes, the model is installed to /var/lib/jarvis/wakewords/ and you
# set it as the wake word in home/modules/jarvis.nix:
#
#   services.jarvis.wakeWord = "hey_friday";
#
# then rebuild. openWakeWord picks up custom models from that directory, which
# modules/jarvis.nix already passes via customModelsDirectories.

set -euo pipefail

PHRASE="${1:-}"
if [[ -z "$PHRASE" ]]; then
    echo "usage: $0 \"wake phrase\"" >&2
    echo "example: $0 \"hey friday\"" >&2
    exit 1
fi

# openWakeWord names models with underscores; keep the mapping predictable.
SLUG="$(echo "$PHRASE" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '_' | sed 's/^_//;s/_$//')"
WORKDIR="${JARVIS_TRAIN_DIR:-$HOME/.cache/jarvis/wakeword-training}"
INSTALL_DIR="/var/lib/jarvis/wakewords"

echo "Phrase : $PHRASE"
echo "Model  : $SLUG"
echo "Workdir: $WORKDIR"
echo

# openWakeWord's training stack pins a lot of ML dependencies that are painful to
# express as a Nix derivation and that you only need once. A throwaway venv is
# the pragmatic choice here — nothing in the running system depends on it, and
# the only artefact that escapes is the .onnx model.
if ! command -v uv >/dev/null 2>&1; then
    echo "error: uv is not on PATH (it is in home/modules/development.nix)" >&2
    exit 1
fi

mkdir -p "$WORKDIR"
cd "$WORKDIR"

if [[ ! -d openwakeword ]]; then
    echo "==> Fetching openWakeWord"
    git clone --depth 1 https://github.com/dscripka/openWakeWord.git openwakeword
fi

if [[ ! -d piper-sample-generator ]]; then
    echo "==> Fetching the Piper sample generator"
    git clone --depth 1 https://github.com/rhasspy/piper-sample-generator.git
    # The generator needs a Piper checkpoint; this is the one its README pins.
    curl -L -o piper-sample-generator/models/en_US-libritts_r-medium.pt \
        --create-dirs \
        https://github.com/rhasspy/piper-sample-generator/releases/download/v2.0.0/en_US-libritts_r-medium.pt
fi

echo "==> Creating the training environment"
uv venv --python 3.10 .venv
# shellcheck disable=SC1091
source .venv/bin/activate
uv pip install --quiet \
    openwakeword piper-phonemize torch torchaudio onnx onnxruntime \
    "numpy<2" scipy tqdm pyyaml datasets speechbrain acoustics webrtcvad mutagen torchinfo

echo
echo "==> Generating synthetic samples for \"$PHRASE\""
echo "    This is the slow part. 30k positives is enough for a reliable model;"
echo "    raise --max-samples if the trained model misses your voice."
python piper-sample-generator/generate_samples.py \
    "$PHRASE" \
    --model piper-sample-generator/models/en_US-libritts_r-medium.pt \
    --max-samples 30000 \
    --batch-size 100 \
    --output-dir "$WORKDIR/samples/$SLUG"

echo
echo "==> Training the classifier"
# The upstream notebook is the canonical path; its training entry point is
# exposed as a module so it can run headless.
python -m openwakeword.train \
    --model_name "$SLUG" \
    --positive_reference_dir "$WORKDIR/samples/$SLUG" \
    --output_dir "$WORKDIR/models" \
    --steps 50000

MODEL="$WORKDIR/models/$SLUG.onnx"
if [[ ! -f "$MODEL" ]]; then
    echo
    echo "error: training finished but $MODEL does not exist." >&2
    echo "Check the output above — the upstream trainer's flags occasionally" >&2
    echo "change between releases. The notebook at" >&2
    echo "  $WORKDIR/openwakeword/notebooks/automatic_model_training.ipynb" >&2
    echo "is the fallback and produces the same artefact." >&2
    exit 1
fi

echo
echo "==> Installing to $INSTALL_DIR (needs sudo)"
sudo install -Dm644 "$MODEL" "$INSTALL_DIR/$SLUG.onnx"

cat <<EOF

Done. The model is installed as "$SLUG".

Next:
  1. Set it in nixos-config/home/modules/jarvis.nix:

         services.jarvis.wakeWord = "$SLUG";

  2. Add it to the preload list in nixos-config/modules/jarvis.nix so
     openWakeWord keeps it resident:

         extraArgs = [ "--preload-model" "$SLUG" ];

  3. rebuild

If it triggers too easily, raise services.wyoming.openwakeword.threshold;
if it ignores you, lower it. 0.5 is the default.
EOF
