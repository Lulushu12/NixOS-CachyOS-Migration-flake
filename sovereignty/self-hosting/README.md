# Self-Hosting / Home Server

Replacing cloud storage, photo backup, document management, and git hosting
with services you run and back up yourself.

Already enabled: **Jellyfin** (media server) — see `nixos-config/modules/common.nix`.

## Decision: several small apps, private — plus one deliberately public "outbox"

**Personal/private stack** (Tailscale/Headscale-only, never exposed):
**Syncthing** (device sync) + **restic** (backups) + **Immich** (photos) +
**Forgejo** (git).

**Public-facing exception**: **Nextcloud**, scoped down to just Files +
Sharing (no Talk, no Office, no Photos app — Immich already covers that),
used purely as a "casual sharing" outbox for handing a link to someone
outside the tailnet. Fed by a dedicated `~/ToShare/` folder — Nextcloud
only ever sees what's deliberately dropped there, not the rest of the
personal stack, so a Nextcloud compromise doesn't leak anything beyond
what was already meant to be shared.

**Still open**: Nextcloud needs to be reachable by people who *aren't* on
the tailnet, which means real public exposure — a domain, `services.nginx`
+ `security.acme` for TLS, dynamic DNS if there's no static IP, and a
router port-forward. Headscale (see `networking-dns-vpn/`) has no
Funnel/Serve equivalent, so there's no shortcut here. **Deferred to a
dedicated planning session** — this is the one piece of the whole
sovereignty plan that intentionally punches a hole for convenience, and
it deserves its own hardening pass (fail2ban/rate limiting, 2FA, more
aggressive patch cadence) before it goes live.

### Why several small apps over one all-in-one platform

Nextcloud *could* have covered files+photos+git in one system, but since
Immich (photos) and Forgejo (git) were independently decided as the
best-of-breed picks regardless, Nextcloud couldn't actually consolidate
anything — it would sit alongside them, not replace them. That collapsed
its unique value down to "files + public share links," which doesn't
justify running all of Nextcloud's heavier PHP/Postgres/Redis stack for
the whole home-server story. Small apps also match this repo's existing
"module isolation" philosophy (see `nixos-config/modules/`) — smaller
blast radius per service, independent update cycles.

### Company-values check

- **Syncthing**: no company, MPL-2.0, community-governed.
- **restic**: BSD-2, community/individual-maintainer led.
- **Immich**: joined **FUTO** (a nonprofit backing open-source alternatives
  to Big Tech) in 2024, specifically so maintainers could go full-time
  *without* introducing paid tiers or closed features. AGPLv3. When the
  community pushed for funding transparency, the team answered directly
  and publicly — a good sign, not a red flag.
- **Forgejo**: exists because its community forked away from **Gitea
  Ltd.** (a for-profit company) specifically to stay under nonprofit
  governance (**Codeberg e.V.**) — directly aligned with these values.
- **Nextcloud GmbH**: founded in 2016 when Frank Karlitschek quit as
  ownCloud's CTO over ownCloud Inc.'s VC-driven commercial drift, then
  forked the project. Bootstrapped and profitable since 2016, no VC ever.

## Candidates considered

| Tool | Replaces | nixpkgs | NixOS option | Notes |
|---|---|---|---|---|
| **Syncthing ✅** | Dropbox / Google Drive | ✅ `pkgs.syncthing` | `services.syncthing` | **Decided.** P2P sync, personal devices only. |
| **restic ✅** | Backblaze/iCloud backup lock-in | ✅ `pkgs.restic` | `services.restic.backups.<name>` | **Decided.** Encrypted, incremental, to a remote you control the keys for. |
| **Immich ✅** | Google Photos / iCloud Photos | ✅ `pkgs.immich` | `services.immich` | **Decided.** Auto-backup + ML search, wants real storage. |
| **Forgejo ✅** | GitHub (private/personal repos) | ✅ `pkgs.forgejo` | `services.forgejo` | **Decided.** Tailscale/Headscale-only. |
| **Nextcloud ✅ (scoped)** | Sending files to people outside the tailnet | ✅ `pkgs.nextcloud*` | `services.nextcloud` | **Decided**, but blocked on domain/exposure planning. Files+Sharing app only. |
| Paperless-ngx | Scanned-document cloud services | ✅ `pkgs.paperless-ngx` | `services.paperless` | Not decided yet — revisit later if wanted. |

## Module stubs

`nixos-config/modules/sovereignty/self-hosting.nix` — Syncthing, restic,
Immich, and Forgejo stubs, all `enable = false` by default. Nextcloud has
no stub yet — waiting on the domain/exposure decision.
