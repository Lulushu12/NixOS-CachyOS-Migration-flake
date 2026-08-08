# Digital sovereignty: self-hosting (NAS/sync, backups, photos, git).
# See sovereignty/self-hosting/README.md for the decision writeup.
#
# DECIDED: Syncthing + restic + Immich + Forgejo for personal/private use
# (Tailscale/Headscale-only, never exposed). Nextcloud was also decided on,
# scoped down to Files+Sharing only, as a deliberately public "outbox" for
# casual sharing with people outside the tailnet — fed by a one-way
# ~/ToShare/ folder, not given access to the rest of this data. It's NOT
# stubbed below yet: it needs a domain + reverse proxy + ACME cert, which
# is still an open planning question (see the README).
#
# Everything here is off by default. Flip `enable = true` on the pieces you
# want, then uncomment this module's import in hosts/nixos/default.nix.

{ pkgs, ... }:

{
  # ── Syncthing (Dropbox/Google Drive replacement) ─────────────────────────────
  # Web UI at http://localhost:8384 once enabled. Add devices/folders there
  # or declaratively via services.syncthing.settings.
  services.syncthing = {
    enable = false;
    user = "radu";
    dataDir = "/home/radu/Syncthing";
    openDefaultPorts = true;
  };

  # ── restic backups (encrypted, incremental) ──────────────────────────────────
  # Fill in `repository` and put the password in a file outside the store
  # (e.g. via sops-nix — see modules/sovereignty/identity-secrets.nix) before
  # enabling. Never commit passwordFile contents to git.
  services.restic.backups.home = {
    enable = false;
    paths = [ "/home/radu/Documents" "/home/radu/Syncthing" ];
    repository = "sftp:user@your-backup-host:/backups/nixos";
    passwordFile = "/run/secrets/restic-password";
    initialize = true;
    timerConfig = {
      OnCalendar = "daily";
      Persistent = true;
    };
  };

  # ── Immich (Google Photos / iCloud Photos replacement) ───────────────────────
  # Wants real storage — point mediaLocation at the HDD mount already defined
  # in hosts/nixos/default.nix, not the root partition.
  services.immich = {
    enable = false;
    mediaLocation = "/home/radu/HDD/immich";
    openFirewall = true;
  };

  # ── Forgejo (self-hosted git, GitHub replacement for private repos) ──────────
  # Tailscale/Headscale-only — no reason to expose this publicly.
  services.forgejo = {
    enable = false;
    settings.server = {
      DOMAIN = "git.internal";
      HTTP_PORT = 3001;
    };
  };
}
