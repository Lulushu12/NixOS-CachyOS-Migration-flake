# Identity, Auth & Secrets

Owning your password vault, not scattering secrets in plaintext config
files, and (optionally) your own single sign-on.

## Candidates

| Tool | Replaces | nixpkgs | NixOS option | Effort | Notes |
|---|---|---|---|---|---|
| KeePassXC | LastPass/1Password (fully local) | ✅ `pkgs.keepassxc` | n/a — just `home.packages` | Trivial | No server at all. Sync the `.kdbx` file via Syncthing if you want it on multiple devices. Simplest possible answer to "own your passwords." |
| Vaultwarden | LastPass/1Password/Bitwarden cloud | ✅ `pkgs.vaultwarden` | `services.vaultwarden` | Low | Bitwarden-protocol-compatible server — official Bitwarden apps/browser extensions work unmodified, just point them at your server. Best balance of convenience and control. |
| sops-nix | Secrets sitting in plaintext in this repo | flake input (not nixpkgs) | n/a | Low-Medium | Lets you commit encrypted secrets (age/GPG) to this very flake instead of keeping them out-of-repo. Worth adding once you start self-hosting things that need API keys/passwords in config. |
| Authelia | Google/Microsoft SSO for self-hosted apps | ✅ `pkgs.authelia` | `services.authelia` | Medium | Adds a login+2FA gate in front of other self-hosted services (Nextcloud, Forgejo, etc). Only useful once you have more than one or two self-hosted web apps to protect. |
| Keycloak | Full enterprise IdP (Okta/Auth0) | ✅ `pkgs.keycloak` | `services.keycloak` | High | Overkill for a personal setup — mentioned for completeness only. |

## Recommendation

**Vaultwarden** is the highest-leverage item in this entire plan: one
systemd service, official client apps everywhere, and it immediately
removes your password data from a third party's cloud. Add **sops-nix**
as soon as any other sovereignty module needs a secret (API token, admin
password) so it doesn't end up committed in plaintext. Skip Authelia/Keycloak
until you actually have multiple self-hosted apps worth gating.

## Module stub

`nixos-config/modules/sovereignty/identity-secrets.nix` — Vaultwarden stub,
`enable = false` by default. (KeePassXC is just a package — add it directly
to `home/radu.nix` when wanted, no module needed.)
