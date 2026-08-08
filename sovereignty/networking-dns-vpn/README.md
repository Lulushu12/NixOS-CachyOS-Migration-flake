# Networking, DNS & VPN

Reducing reliance on your ISP's DNS, ad/tracker networks, and third-party
VPN coordination servers.

## Decision: Headscale + AdGuard Home + Unbound

- **Headscale** replaces Tailscale's hosted coordination server — the
  Tailscale *client* stays exactly the same (it's already FOSS), only the
  control plane moves from Tailscale Inc.'s SaaS to something self-hosted.
- **AdGuard Home** for DNS-level ad/tracker blocking, chosen over Blocky
  specifically for its web dashboard (query log, per-device rules).
- **Unbound** set as AdGuard Home's upstream resolver — full recursive
  resolution straight to root/TLD servers, so no third party (not even a
  privacy-focused one like Cloudflare) ever sees the query stream.

### Why, given the actual requirements

Tailscale's SaaS coordination dependency was flagged as a real concern
("bothers me, want it self-hosted"), a dashboard mattered more than a
config file for the DNS blocker, and full recursive resolution was
preferred over trusting any public resolver — Blocky and public
DNS-as-upstream were both ruled out on those grounds, not on merit.

### Company-values check — all three came back clean

- **AdGuard**: bootstrapped and privately owned since 2009, founder-led
  (CEO Andrey Meshkov, one of three co-founders), no VC/PE money ever
  raised, ~71 employees, profitable (~$5.4M ARR). AdGuard Home is GPL-3.0.
- **Headscale**: community-maintained, formally independent of Tailscale
  Inc. One maintainer is also a Tailscale employee who contributes on his
  own time, reviewed by the other maintainers — fully transparent about
  it, same pattern as Vaultwarden's relationship to Bitwarden. BSD-3-Clause.
- **Unbound**: built by **NLnet Labs**, an actual Dutch nonprofit
  foundation focused on core internet infrastructure — not a company at
  all. Modified BSD License. The cleanest governance profile of anything
  looked at across this whole plan.

> Note: **Pi-hole was ruled out** — no native NixOS module, since it
> assumes a mutable Debian-style filesystem and installs itself
> imperatively, which fights the NixOS declarative model. AdGuard Home
> gives the same result declaratively.

## Candidates considered

| Tool | Replaces | nixpkgs | NixOS option | Notes |
|---|---|---|---|---|
| **AdGuard Home ✅** | ISP DNS / third-party ad-block DNS | ✅ `pkgs.adguardhome` | `services.adguardhome` | **Decided.** Dashboard + query log. |
| **Unbound ✅** | Public recursive resolvers (Google/Cloudflare) | ✅ `pkgs.unbound` | `services.unbound` | **Decided.** Sits behind AdGuard Home as upstream. |
| **Headscale ✅** | Tailscale's hosted coordination server | ✅ `pkgs.headscale` | `services.headscale` | **Decided.** Client unchanged, only the control plane moves. Needs its own public reachability, though — a phone on cellular away from home has to reach it before it's *on* the tailnet, so this needs a domain + reverse proxy + TLS cert, same open question as the Nextcloud outbox in `self-hosting/README.md`. Also: no Tailscale Funnel/Serve equivalent, if that ever mattered for exposing something through the tailnet later. |
| Blocky | ISP DNS / third-party ad-block DNS | ✅ `pkgs.blocky` | `services.blocky` | Passed on — config-file only, no dashboard. |
| Plain WireGuard | Commercial VPN providers | ✅ `pkgs.wireguard-tools` | `networking.wireguard.interfaces` | Ruled out — Headscale already removes the SaaS dependency without giving up Tailscale's NAT-traversal convenience. |

## Module stub

`nixos-config/modules/sovereignty/networking.nix` — AdGuard Home and
Unbound stubs, `enable = false` by default. Headscale doesn't have a
stub yet (bigger lift — needs its own domain/cert plus repointing every
device's Tailscale client at it); add when ready to tackle it.
