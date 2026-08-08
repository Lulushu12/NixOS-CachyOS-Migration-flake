# Identity, Auth & Secrets

Owning your password vault, not scattering secrets in plaintext config
files, and (optionally) your own single sign-on.

## Decision: Vaultwarden, Tailscale-only

**Vaultwarden** (self-hosted, reachable only over Tailscale/Headscale — no
public `DOMAIN`, no port-forwarding), used with the **official Bitwarden**
apps/browser extensions on phone and PC.

### Why, given the actual requirements

- Needed: passwords on PC + phone, autofill matters a lot, an always-on
  Tailscale-only service is fine, but the vault being unreachable for even
  a few hours is unacceptable.
- **KeePassXC** (a local `.kdbx` file, zero server) was the values-purest
  option — no company anywhere in the stack — but loses the seamless
  autofill that mattered most here.
- **Vaultwarden resolves the "downtime unacceptable" concern** in a way
  that isn't obvious upfront: official Bitwarden clients keep an
  **encrypted local cache** after first sync and support **offline
  unlock** with your master password. If the server or tailnet is briefly
  down, already-synced devices still unlock and read every password —
  you just can't add/edit until it's back. Same safety net as KeePassXC,
  with autofill everywhere.

### The company-values wrinkle

- **Vaultwarden itself** (the server) is fully independent and
  community-maintained — no company owns it, licensed **AGPL-3.0**
  specifically to prevent a closed-source SaaS fork.
- **Bitwarden Inc.** (the company shipping the client apps you'd actually
  use daily) is VC/PE-backed — a $100M growth round in 2022 led by PSG.
  In 2026, founder-CEO Michael Crandell moved to an advisory role,
  replaced by Michael Sullivan, whose background is M&A-heavy (led a $1B
  PE sale at Acquia, a $1B PE investment at Insightsoftware) — the kind of
  résumé that signals "brought in for an exit," not "brought in to grow
  the product." The CFO was replaced the same year. Bitwarden also briefly
  scrubbed "Always free" from its pricing page and quietly dropped
  "Inclusion" from its stated company values (restored/renamed after
  public pushback).
- **Accepted risk**: the client apps are GPL-3.0 (open source) today —
  real insurance if Bitwarden Inc.'s trajectory keeps sliding, since the
  code can be forked (this is literally how Vaultwarden itself came to
  exist once before) and vault data is exportable to any compatible tool.
  Given autofill mattered more here than running zero services, this
  tradeoff was accepted over KeePassXC's cleaner-but-rougher alternative.

## Candidates considered

| Tool | Replaces | nixpkgs | NixOS option | Effort | Notes |
|---|---|---|---|---|---|
| **Vaultwarden ✅** | LastPass/1Password/Bitwarden cloud | ✅ `pkgs.vaultwarden` | `services.vaultwarden` | Low | **Decided.** Bitwarden-protocol-compatible — official apps/extensions work unmodified. |
| KeePassXC | LastPass/1Password (fully local) | ✅ `pkgs.keepassxc` | n/a — `home.packages` | Trivial | Passed on — no server at all, but autofill/multi-device UX loses to Vaultwarden. |
| sops-nix | Secrets sitting in plaintext in this repo | flake input (not nixpkgs) | n/a | Low-Medium | Next step once Vaultwarden is enabled — needed for its `ADMIN_TOKEN`. |
| Authelia | Google/Microsoft SSO for self-hosted apps | ✅ `pkgs.authelia` | `services.authelia` | Medium | Deferred — only useful once there are multiple self-hosted web apps to gate. |
| Keycloak | Full enterprise IdP (Okta/Auth0) | ✅ `pkgs.keycloak` | `services.keycloak` | High | Ruled out — overkill for a personal setup. |

## Module stub

`nixos-config/modules/sovereignty/identity-secrets.nix` — Vaultwarden
stub, `enable = false` by default, `DOMAIN` set to a tailnet address (not
a public one). Add sops-nix as a flake input before flipping this on, so
`ADMIN_TOKEN` isn't committed in plaintext.
