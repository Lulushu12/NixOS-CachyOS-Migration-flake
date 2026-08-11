# Wolf — multi-tenant game streaming (games-on-whales.github.io/wolf).
#
# Where Sunshine (streaming.nix) shares YOUR desktop with one seat, Wolf gives
# every connecting Moonlight client its own isolated containerized session:
# own virtual desktop, own Steam login, own game instance — all sharing the
# GPU. This is the "several people playing separately on one machine" mode.
#
# ─── Port conflict with Sunshine — read this first ──────────────────────────
# Wolf and Sunshine both speak the Moonlight protocol on the SAME ports
# (TCP 47984/47989/48010, UDP 47998+). They cannot listen simultaneously.
# Sunshine autostarts with your desktop session; Wolf stays off until asked.
# Switch between them with the helper commands installed by this module:
#
#   wolf-on    # stops Sunshine (your user service), starts Wolf
#   wolf-off   # stops Wolf, restarts Sunshine
#
# ─── First-time setup ───────────────────────────────────────────────────────
# 1. Rebuild, run `wolf-on`.
# 2. Pair each client: when Moonlight connects, it shows a PIN. Fetch the
#    pairing link from the Wolf log and open it in a browser on the host:
#      sudo journalctl -u docker-wolf | grep -F 'http://localhost:47989/pin'
#    Enter the client's PIN there.
# 3. In Moonlight, each client now sees Wolf's app list (Steam, RetroArch,
#    Firefox, a plain desktop…). First launch of each app pulls its container
#    image — expect a multi-GB download per app type.
# 4. Per-session state (Steam logins, saves) persists under /etc/wolf.
#
# ─── NVIDIA note ────────────────────────────────────────────────────────────
# GPU access is passed through via the NVIDIA container toolkit (CDI).
# If Wolf logs GPU errors on startup, consult the current GoW NVIDIA docs:
# https://games-on-whales.github.io/wolf/stable/user/quickstart.html
#
# ─── Capacity expectations (RTX 2070 SUPER, 8 GB VRAM, Ryzen 3700X) ────────
# The binding constraint is VRAM: each session fully renders its own game.
# Two light/medium games run comfortably; two AAA titles will not. NVENC
# allows up to 8 encode sessions on current drivers — you'll run out of
# VRAM long before you run out of encoder.

{ config, pkgs, ... }:

{
  # ── Container runtime ──────────────────────────────────────────────────────
  # Wolf itself runs in Docker AND talks to the Docker socket to spawn one
  # app container per client session — so Docker (not Podman) is required.
  virtualisation.docker.enable = true;
  virtualisation.oci-containers.backend = "docker";

  # Expose the NVIDIA GPU to containers via CDI (--device=nvidia.com/gpu=all).
  hardware.nvidia-container-toolkit.enable = true;

  # Virtual gamepads / mice / keyboards for each session are created through
  # uinput on the host.
  boot.kernelModules = [ "uinput" ];

  # ── The Wolf container ─────────────────────────────────────────────────────
  # Mirrors the upstream docker-compose from the Wolf quickstart.
  virtualisation.oci-containers.containers.wolf = {
    image = "ghcr.io/games-on-whales/wolf:stable";

    environment = {
      XDG_RUNTIME_DIR = "/tmp/sockets";
      HOST_APPS_STATE_FOLDER = "/etc/wolf";
    };

    volumes = [
      "/etc/wolf:/etc/wolf:rw"                       # config + per-user state
      "/tmp/sockets:/tmp/sockets:rw"                 # wayland/pulse sockets
      "/var/run/docker.sock:/var/run/docker.sock:rw" # spawn session containers
      "/dev:/dev:rw"
      "/run/udev:/run/udev:rw"
    ];

    extraOptions = [
      "--network=host"                    # Moonlight ports + mDNS discovery
      "--device-cgroup-rule=c 13:* rmw"   # input device hot-plug (uinput)
      "--device=/dev/dri"
      "--device=/dev/uinput"
      "--device=nvidia.com/gpu=all"       # CDI: driver + all NVIDIA devices
    ];

    # Off by default — Sunshine owns the Moonlight ports day-to-day.
    # `wolf-on` starts it; survives until `wolf-off` or reboot.
    autoStart = false;
  };

  # ── Sunshine ⇄ Wolf switch helpers ─────────────────────────────────────────
  environment.systemPackages = [
    (pkgs.writeShellScriptBin "wolf-on" ''
      systemctl --user stop sunshine 2>/dev/null || true
      sudo systemctl start docker-wolf
      echo "Wolf is up — Sunshine stopped. Clients pair against Wolf now."
      echo "Pairing links: sudo journalctl -u docker-wolf -f | grep pin"
    '')
    (pkgs.writeShellScriptBin "wolf-off" ''
      sudo systemctl stop docker-wolf
      systemctl --user start sunshine 2>/dev/null || true
      echo "Wolf stopped — Sunshine restarted on your desktop session."
    '')
  ];

  # Wolf's session containers occasionally need firewall room beyond the
  # Moonlight ports Sunshine already opened (streaming.nix openFirewall);
  # video/audio for extra concurrent sessions use these ranges.
  networking.firewall.allowedUDPPortRanges = [
    { from = 48100; to = 48110; }   # video (one port per active session)
    { from = 48200; to = 48210; }   # audio
  ];
}
