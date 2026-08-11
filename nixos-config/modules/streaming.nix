# Self-hosted game streaming — a personal "GeForce Now".
#
# Sunshine runs on this machine and streams the desktop / games with NVENC
# hardware encoding on the NVIDIA GPU. Any device running the Moonlight
# client (Android, iOS, Windows, macOS, Linux, Steam Deck, LG/Android TV,
# even a browser) connects to it and gets a low-latency video stream with
# full controller / mouse / keyboard passthrough.
#
# ─── First-time setup ────────────────────────────────────────────────────────
# 1. Rebuild, then log into the desktop (Sunshine starts with your session).
# 2. Open the Sunshine web UI: https://localhost:47990
#    (self-signed certificate — accept the browser warning)
#    Create a username/password on first visit.
# 3. Install Moonlight on the client device: https://moonlight-stream.org
#    On the same network it auto-discovers this PC. Click it, and Moonlight
#    shows a 4-digit PIN — enter that PIN in the Sunshine web UI under "PIN".
# 4. Stream "Desktop", or add specific games under Applications in the web UI
#    (e.g. command `steam steam://rungameid/<appid>` for a Steam title).
#
# ─── Streaming from outside your home network ───────────────────────────────
# Do NOT port-forward Sunshine to the open internet. Use a mesh VPN instead:
# enable Tailscale below (also install Tailscale on the client device), then
# in Moonlight add the host manually using its Tailscale IP (100.x.y.z).
#
# ─── Performance notes ──────────────────────────────────────────────────────
# • RTX 2070 SUPER NVENC handles 1080p60 / 1440p60 easily; start with
#   20–40 Mbit/s bitrate in Moonlight settings and raise until artifacts.
# • Wired Ethernet on the host matters more than on the client.
# • On Plasma Wayland, capture uses KMS — that's why capSysAdmin is on.

{ config, pkgs, ... }:

{
  services.sunshine = {
    enable = true;

    # Start automatically with the graphical session (user service).
    autoStart = true;

    # Grants CAP_SYS_ADMIN to the Sunshine binary — required for KMS screen
    # capture on Wayland (and for NvFBC on X11). Without it only slow
    # software capture is available.
    capSysAdmin = true;

    # Opens the ports Moonlight needs:
    #   TCP 47984 (HTTPS), 47989 (HTTP), 47990 (web UI), 48010 (RTSP)
    #   UDP 47998-48000 (video/audio/control), 48002, 48010
    openFirewall = true;
  };

  # mDNS/Avahi lets Moonlight clients on the LAN auto-discover this host —
  # no need to type an IP address.
  services.avahi = {
    enable = true;
    publish = {
      enable = true;
      userServices = true;
    };
  };

  # ── Remote access via Tailscale (optional) ─────────────────────────────────
  # Uncomment to stream from outside the LAN without exposing any ports.
  # After rebuild, run `sudo tailscale up` once and sign in; install the
  # Tailscale app on your client device with the same account.
  # services.tailscale.enable = true;

  environment.systemPackages = with pkgs; [
    moonlight-qt   # Moonlight client — handy for testing the stream locally
                   # and for streaming FROM another PC when travelling.
  ];
}
