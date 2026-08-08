# Digital sovereignty: password vault.
# See sovereignty/identity-auth-secrets/README.md for the full comparison.
#
# Off by default; uncomment this module's import in hosts/nixos/default.nix
# once ready.

{ pkgs, ... }:

{
  # ── Vaultwarden (self-hosted Bitwarden-compatible server) ────────────────────
  # Official Bitwarden apps/browser extensions work unmodified — just point
  # them at this server's address instead of bitwarden.com.
  #
  # ADMIN_TOKEN must not be committed in plaintext. Once sops-nix (or
  # equivalent) is set up, replace this with an EnvironmentFile pointing at
  # a decrypted secret instead of a literal value here.
  services.vaultwarden = {
    enable = false;
    dbBackend = "sqlite";
    config = {
      DOMAIN = "https://vault.example.com";
      SIGNUPS_ALLOWED = false;
      ROCKET_PORT = 8222;
    };
  };
}
