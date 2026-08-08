# Digital Sovereignty Plan

A running list of "own your data / own your infrastructure" solutions,
scoped to what's realistically packaged and maintainable on NixOS with this
flake (`nixos-config/`). The goal isn't ideological purity — it's reducing
dependence on third parties for things that matter (backups, chat, DNS,
secrets) while keeping the system boring enough to actually maintain solo.

## Status: all four categories decided, nothing implemented yet

Every category below has a locked-in decision, reached by weighing actual
needs (device count, downtime tolerance, autofill, sharing) against the
governance/company track record of each option — see each category's
README for the reasoning and the diligence behind picks like Vaultwarden,
Headscale, and AdGuard Home. **Nothing is enabled yet**: all module stubs
in `nixos-config/modules/sovereignty/*.nix` still have `enable = false`,
and their imports are still commented out in `hosts/nixos/default.nix`.
Flipping them on is a separate, deliberate next step.

| Category | Decision | Status |
|---|---|---|
| Identity, auth & secrets | Vaultwarden (Tailscale-only) + official Bitwarden apps | Decided, not enabled |
| Networking, DNS & VPN | Headscale + AdGuard Home + Unbound | Decided, not enabled |
| Self-hosting | Syncthing + restic + Immich + Forgejo + scoped-down Nextcloud (public outbox) | Decided; Nextcloud's public exposure (domain/reverse proxy) still needs planning |
| Comms & browser | Zen (kept, to be hardened) + self-hosted SearXNG + Signal (kept, no forced migration) | Decided, not enabled |

## How this is organized

Each category below has its own folder with a table of candidate tools,
the diligence behind the pick (including who's actually behind each
project — company, VC backing, nonprofit, or pure community), and the
final decision. Matching NixOS module *stubs* live in
`nixos-config/modules/sovereignty/*.nix` — written but disabled, so
nothing changes on your next rebuild until you deliberately opt in. To
enable one:

1. Read the category doc for the "Decision" section — the reasoning is there.
2. Flip the relevant option to `enable = true` in the module file.
3. Uncomment its import line in `nixos-config/hosts/nixos/default.nix`.
4. `sudo nixos-rebuild switch --flake /etc/nixos/nixos-config#nixos`.

## Already in place

Two things this config already does that count as sovereignty wins —
tracked here so they're not duplicated below:

| Tool | Where | What it replaces |
|---|---|---|
| Tailscale (client) | `nixos-config/modules/common.nix` | Exposing services directly to the internet / relying on a static public IP |
| Jellyfin | `nixos-config/modules/common.nix` | Netflix/Plex-style subscription media, keeps your library local |

Note: Tailscale's *coordination server* is being replaced by self-hosted
Headscale (see `networking-dns-vpn/`) — the client itself stays the same
either way, since it's already FOSS.

## Categories

- [`self-hosting/`](./self-hosting/README.md) — NAS/file sync, backups, photos, docs, git
- [`networking-dns-vpn/`](./networking-dns-vpn/README.md) — DNS-level blocking, recursive resolvers, self-hosted VPN coordination
- [`identity-auth-secrets/`](./identity-auth-secrets/README.md) — password manager, SSO, secrets-in-git
- [`comms-browser/`](./comms-browser/README.md) — chat, search, browser, email

## Implementation order

Roughly cheapest-and-safest first, matching the decisions above:

1. **Vaultwarden** (identity) — single highest-leverage item, one systemd service, Tailscale-only.
2. **Headscale + AdGuard Home + Unbound** (networking) — set-and-forget once running, and Headscale first means everything after it can assume the tailnet is self-hosted.
3. **Syncthing + restic** (self-hosting) — replaces Dropbox/Google Drive and covers backups before anything else stores data worth losing.
4. **SearXNG** (comms) — stateless, near-zero maintenance, safe to add any time.
5. **Immich + Forgejo** (self-hosting) — once the backup story above is solid.
6. **Nextcloud outbox** (self-hosting) — blocked on the domain/reverse-proxy/ACME planning session, since it's the one component that needs real public exposure.

## Diligence approach

For anything with real day-to-day reliance (password vault, DNS, VPN
coordination), we checked who's actually behind it — VC-backed company,
bootstrapped company, nonprofit, or pure community project — because that
shapes long-term risk (acquisition, monetization pivots, abandonment)
differently than technical merits alone. Notable findings baked into the
decisions:

- **Bitwarden Inc.** (whose open-source client apps Vaultwarden's decision relies on) is VC/PE-backed and went through a leadership shakeup in 2026 with M&A-flavored optics. Accepted risk, mitigated by the code being open source and the vault being exportable/forkable — see `identity-auth-secrets/README.md`.
- **AdGuard**, **Headscale**, and **Unbound** (NLnet Labs, an actual nonprofit) all checked out clean — no VC, no red flags.
- **Forgejo** exists specifically because its community forked away from Gitea Ltd. (a for-profit company) to stay under nonprofit governance (Codeberg e.V.) — directly aligned with these values.
- **Nextcloud GmbH** has a similar origin: founded when Frank Karlitschek left ownCloud Inc. over its VC-driven commercial drift; bootstrapped and profitable since 2016.
- **Immich** joined FUTO (a nonprofit) in 2024 specifically to fund development without paid tiers or closed features.
- **Zen Browser** is fully community-run (no company, no VC) — see `comms-browser/README.md` for how it compares to LibreWolf and how to hardened it further.

## A note on realism

Some categories (self-hosted email, self-hosted chat for reaching
WhatsApp/Instagram/Messenger contacts) were explicitly ruled out — see
each category doc for why. Sovereignty here means owning what you
realistically control, not chasing purity where the tradeoff isn't worth it.
