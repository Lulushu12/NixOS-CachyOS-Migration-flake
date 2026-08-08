# Digital sovereignty: password vault.
# See sovereignty/identity-auth-secrets/README.md for the decision writeup.
#
# DECIDED: Vaultwarden, reachable only over Tailscale/Headscale — no public
# DOMAIN, no port-forwarding. Official Bitwarden apps/extensions on
# phone+PC (their local encrypted cache covers the "downtime is
# unacceptable" requirement: they still unlock offline if the server or
# tailnet is briefly unreachable). KeePassXC was considered and passed on —
# autofill mattered more here than running zero services.
#
# Off by default; uncomment this module's import in hosts/nixos/default.nix
# once ready.

{ pkgs, ... }:

{
  # ── Vaultwarden (self-hosted Bitwarden-compatible server) ────────────────────
  # Official Bitwarden apps/browser extensions work unmodified — just point
  # them at this host's Tailscale/Headscale address instead of bitwarden.com.
  #
  # ADMIN_TOKEN must not be committed in plaintext. Once sops-nix is set up,
  # replace this with an EnvironmentFile pointing at a decrypted secret
  # instead of a literal value here.
  services.vaultwarden = {
    enable = false;
    dbBackend = "sqlite";
    config = {
      DOMAIN = "https://vault.nixos.tailnet";  # tailnet MagicDNS name, not a public domain
      SIGNUPS_ALLOWED = false;
      ROCKET_PORT = 8222;
    };
  };
}
