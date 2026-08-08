# Digital sovereignty: DNS blocking and recursive resolution.
# See sovereignty/networking-dns-vpn/README.md for the decision writeup.
#
# DECIDED: AdGuard Home (dashboard) with Unbound as its upstream resolver —
# picked over Blocky specifically for the web UI/query-log dashboard.
# Off by default; uncomment this module's import in hosts/nixos/default.nix
# once ready.

{ pkgs, ... }:

{
  # ── AdGuard Home (DNS-level ad/tracker blocking, with dashboard) ─────────────
  # Web UI at http://localhost:3000 for first-run setup (blocklists, upstream).
  # Point your router/NetworkManager DNS at this host once enabled.
  services.adguardhome = {
    enable = false;
    openFirewall = true;
    settings = {
      dns = {
        # Unbound below, not Cloudflare/Google — no third party ever sees
        # the query stream.
        upstream_dns = [ "127.0.0.1:5053" ];
      };
    };
  };

  # ── Unbound (full recursive resolver — AdGuard Home's upstream) ──────────────
  # Queries root/TLD servers directly instead of forwarding to a public
  # resolver. Slower first lookups, but nobody downstream sees your queries.
  services.unbound = {
    enable = false;
    settings = {
      server = {
        interface = [ "127.0.0.1" ];
        port = 5053; # keep off 53 — AdGuard Home owns that port
      };
    };
  };
}
