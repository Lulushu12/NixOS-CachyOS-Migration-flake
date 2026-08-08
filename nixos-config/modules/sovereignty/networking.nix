# Digital sovereignty: DNS blocking and recursive resolution.
# See sovereignty/networking-dns-vpn/README.md for the full comparison.
#
# Pick ONE of Blocky/AdGuard Home, not both — they both want port 53.
# Off by default; uncomment this module's import in hosts/nixos/default.nix
# once you've picked one.

{ pkgs, ... }:

{
  # ── Blocky (DNS-level ad/tracker blocking) ────────────────────────────────────
  # Config-file based, no web UI. Point your router/NetworkManager DNS at
  # 127.0.0.1 once this is enabled and working.
  services.blocky = {
    enable = false;
    settings = {
      ports.dns = 53;
      upstreams.groups.default = [
        # Cloudflare/Google as a starting point — swap for Unbound below once
        # that's running, to stop relying on any third-party resolver at all.
        "1.1.1.1"
        "8.8.8.8"
      ];
      blocking.blackLists.ads = [
        "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
      ];
    };
  };

  # ── Unbound (full recursive resolver — no third-party DNS dependency) ────────
  # Queries root/TLD servers directly instead of forwarding to Cloudflare/Google.
  # Slower first lookups, but nobody downstream sees your query stream.
  services.unbound = {
    enable = false;
    settings = {
      server = {
        interface = [ "127.0.0.1" ];
        port = 5053; # keep off 53 so it can sit behind Blocky as its upstream
      };
    };
  };
}
