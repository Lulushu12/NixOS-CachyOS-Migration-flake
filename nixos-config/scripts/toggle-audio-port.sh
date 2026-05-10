#!/usr/bin/env bash

export XDG_RUNTIME_DIR="/run/user/1000"
export PATH="/run/current-system/sw/bin:/run/wrappers/bin:$PATH"

SINK="alsa_output.pci-0000_0b_00.4.analog-stereo"
NOTIFY_SEND="notify-send"

CURRENT_PORT=$(pactl list sinks | awk -v sink="$SINK" '
  $0 ~ "Name: "sink {found=1}
  found && /Active Port:/ {print $3; exit}
')

if [ "$CURRENT_PORT" = "analog-output-headphones" ]; then
    pactl set-sink-port "$SINK" analog-output-lineout
    [ -n "$NOTIFY_SEND" ] && "$NOTIFY_SEND" -a "Trumpet" "Audio Output" "Switched to Speakers"
elif [ "$CURRENT_PORT" = "analog-output-lineout" ]; then
    pactl set-sink-port "$SINK" analog-output-headphones
    [ -n "$NOTIFY_SEND" ] && "$NOTIFY_SEND" -a "Trumpet" "Audio Output" "Switched to Headphones"
fi
