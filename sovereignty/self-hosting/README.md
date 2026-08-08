# Self-Hosting / Home Server

Replacing cloud storage, photo backup, document management, and git hosting
with services you run and back up yourself.

Already enabled: **Jellyfin** (media server) — see `nixos-config/modules/common.nix`.

## Candidates

| Tool | Replaces | nixpkgs | NixOS option | Effort | Notes |
|---|---|---|---|---|---|
| Syncthing | Dropbox / Google Drive | ✅ `pkgs.syncthing` | `services.syncthing` | Low | P2P file sync, no server needed at all. Best first pick. |
| restic (+ a remote) | Backblaze/iCloud backup lock-in | ✅ `pkgs.restic` | `services.restic.backups.<name>` | Low | Encrypted, incremental. Pair with a storage box or B2 bucket you control the keys for. |
| Immich | Google Photos / iCloud Photos | ✅ `pkgs.immich` | `services.immich` | Medium | Mobile app has auto-backup like Google Photos. Wants real storage + occasional maintenance. |
| Paperless-ngx | Scanned-document cloud services | ✅ `pkgs.paperless-ngx` | `services.paperless` | Medium | OCR + tagging for scanned mail/receipts. Needs Postgres + Redis (module handles it). |
| Forgejo | GitHub (for private/personal repos) | ✅ `pkgs.forgejo` | `services.forgejo` | Medium | Lightweight, actively maintained Gitea fork. Only worth it if you want repos off GitHub too. |
| Nextcloud | Full Google Workspace replacement | ✅ `pkgs.nextcloud*` | `services.nextcloud` | High | Heaviest option here — covers files+calendar+contacts+office, but also the most moving parts (PHP, nginx, Postgres) to keep patched. Only reach for this if Syncthing+Immich+Paperless individually feel like too many separate apps. |

## Recommendation

Start with **Syncthing + restic**. Both are single static binaries, no
database, near-zero maintenance, and cover the two things that actually
hurt to lose (files, backups). Add Immich once you trust the backup story.
Skip Nextcloud unless the "several small apps" model genuinely bothers you —
it's a lot more surface area to patch and babysit.

## Module stub

`nixos-config/modules/sovereignty/self-hosting.nix` — Syncthing, restic, and
Immich stubs, all `enable = false` by default.
