# Networking, DNS & VPN

Reducing reliance on your ISP's DNS, ad/tracker networks, and third-party
VPN coordination servers.

Already enabled: **Tailscale client** — see `nixos-config/modules/common.nix`.
Coordination currently goes through Tailscale's own servers (see caveat in
`sovereignty/README.md`).

## Candidates

| Tool | Replaces | nixpkgs | NixOS option | Effort | Notes |
|---|---|---|---|---|---|
| Blocky | ISP DNS / third-party ad-block DNS | ✅ `pkgs.blocky` | `services.blocky` | Low | Config-file based, no web UI to babysit. Nix-native feel. |
| AdGuard Home | ISP DNS / third-party ad-block DNS | ✅ `pkgs.adguardhome` | `services.adguardhome` | Low | Same job as Blocky but with a web dashboard — pick one, not both. |
| Unbound | Public recursive resolvers (Google/Cloudflare DNS) | ✅ `pkgs.unbound` | `services.unbound` | Low-Medium | Full recursive resolver — your queries never leave your network to a third party at all. Can run behind Blocky/AdGuard as the upstream. |
| Headscale | Tailscale's hosted coordination server | ✅ `pkgs.headscale` | `services.headscale` | Medium | Self-hosted control plane, same client (`tailscale`) just pointed at your server instead of theirs. Only worth it if the SaaS dependency actually bothers you — the client itself already stays FOSS either way. |
| WireGuard (plain) | Commercial VPN providers | ✅ built into kernel + `pkgs.wireguard-tools` | `networking.wireguard.interfaces` | Medium | Lower-level than Tailscale (manual key/peer management, no NAT traversal magic). Only reach for this over Tailscale if you specifically don't want any coordination server, self-hosted or not. |

> Note: **Pi-hole has no native NixOS module** — it assumes a mutable
> Debian-style filesystem and installs itself imperatively, which fights
> NixOS's model. Blocky or AdGuard Home give the same result declaratively.

## Recommendation

**Blocky** first — it's a single binary, config is a YAML file that fits
naturally into a Nix module, and it can chain to **Unbound** as its upstream
resolver later if you want to drop public DNS resolvers entirely. Leave
Headscale/plain WireGuard alone unless the Tailscale SaaS dependency
specifically bothers you — the maintenance cost is real and the client
already stays FOSS regardless.

## Module stub

`nixos-config/modules/sovereignty/networking.nix` — Blocky and Unbound
stubs, `enable = false` by default.
