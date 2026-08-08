# Digital sovereignty: self-hosted search and chat.
# See sovereignty/comms-browser/README.md for the full comparison.
#
# LibreWolf/Signal/Element are plain packages, not services — add those
# directly to home/radu.nix's home.packages when wanted, no module needed.
#
# Off by default; uncomment this module's import in hosts/nixos/default.nix
# once ready.

{ pkgs, ... }:

{
  # ── SearXNG (self-hosted metasearch, Google/Bing replacement) ────────────────
  services.searx = {
    enable = false;
    settings = {
      server = {
        port = 8888;
        bind_address = "127.0.0.1";
      };
    };
  };

  # ── Matrix Conduit (lightweight self-hosted chat homeserver) ─────────────────
  # Pairs with Element (pkgs.element-desktop) as the client. Only worth
  # running if the people you talk to will actually join you here — don't
  # self-host a chat server for an audience of one.
  services.matrix-conduit = {
    enable = false;
    settings.global = {
      server_name = "example.com";
      port = 6167;
    };
  };
}
