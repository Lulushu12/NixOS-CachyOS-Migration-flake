# Digital Sovereignty Plan

A running list of "own your data / own your infrastructure" solutions,
scoped to what's realistically packaged and maintainable on NixOS with this
flake (`nixos-config/`). The goal isn't ideological purity — it's reducing
dependence on third parties for things that matter (backups, chat, DNS,
secrets) while keeping the system boring enough to actually maintain solo.

## How this is organized

Each category below has its own folder with a table of candidate tools,
their nixpkgs status, and notes. Matching NixOS module *stubs* live in
`nixos-config/modules/sovereignty/*.nix` — they're written but disabled
(`enable = false` / not imported), so nothing changes on your next rebuild
until you deliberately opt in. To enable one:

1. Read the category doc, pick a tool.
2. Flip the relevant option to `enable = true` in the module file.
3. Uncomment its import line in `nixos-config/hosts/nixos/default.nix`.
4. `sudo nixos-rebuild switch --flake /etc/nixos/nixos-config#nixos`.

## Already in place

Two things this config already does that count as sovereignty wins —
tracked here so they're not duplicated below:

| Tool | Where | What it replaces |
|---|---|---|
| Tailscale | `nixos-config/modules/common.nix` | Exposing services directly to the internet / relying on a static public IP |
| Jellyfin | `nixos-config/modules/common.nix` | Netflix/Plex-style subscription media, keeps your library local |

Note: Tailscale's *client* is FOSS but its coordination server is Tailscale's
own SaaS. That's fine for convenience — if full independence from it matters
later, `sovereignty/networking-dns-vpn/` covers self-hosting the coordination
layer with Headscale.

## Categories

- [`self-hosting/`](./self-hosting/README.md) — NAS/file sync, backups, photos, docs, git
- [`networking-dns-vpn/`](./networking-dns-vpn/README.md) — DNS-level blocking, recursive resolvers, self-hosted VPN coordination
- [`identity-auth-secrets/`](./identity-auth-secrets/README.md) — password manager, SSO, secrets-in-git
- [`comms-browser/`](./comms-browser/README.md) — chat, search, browser, email

## Suggested rollout order

Roughly cheapest-and-safest first. No deadline — pick items as they become
useful rather than doing all of them at once.

1. **Password manager** (Vaultwarden) — single most impactful, low maintenance, one systemd service.
2. **DNS blocking** (AdGuard Home or Blocky) — set-and-forget, immediate benefit.
3. **File sync** (Syncthing) — replaces Dropbox/Google Drive for anything that doesn't need public sharing.
4. **Backups** (restic to a remote you control) — do this before you have data you'd regret losing.
5. **Photos** (Immich) — only once storage/backup story above is solid.
6. Everything else (Matrix, SearXNG, Headscale, SSO) — opt in per interest, these have real ongoing maintenance cost.

## A note on realism

Some categories (self-hosted email in particular) are covered in the docs
for completeness but *not* recommended to actually run solo — deliverability
and spam-fighting infrastructure is a full-time job. Each doc calls out
where "sovereign" and "sane" diverge.
