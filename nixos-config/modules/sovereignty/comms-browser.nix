# Digital sovereignty: self-hosted search.
# See sovereignty/comms-browser/README.md for the decision writeup.
#
# DECIDED: SearXNG only. Matrix/Conduit was considered and dropped — no
# audience, everyone we talk to is on WhatsApp/Instagram/Messenger and won't
# switch, so self-hosting a chat homeserver has no payoff right now.
#
# Browser (Zen, kept) and Signal are plain packages, not services — add
# those directly to home/radu.nix's home.packages when wanted, no module
# needed. Zen isn't in nixpkgs proper; see the README for the community
# flake input if you want it managed declaratively.
#
# Off by default; uncomment this module's import in hosts/nixos/default.nix
# once ready.

{ pkgs, ... }:

{
  # ── SearXNG (self-hosted metasearch, aggregates DuckDuckGo + others) ─────────
  # Not a replacement for DuckDuckGo — it queries DuckDuckGo and other
  # engines on your behalf and lets you drop/reweight any of them from one
  # config file, so you're never locked into a single provider.
  services.searx = {
    enable = false;
    settings = {
      server = {
        port = 8888;
        bind_address = "127.0.0.1";
      };
    };
  };
}
