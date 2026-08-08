# Digital sovereignty: self-hosting (NAS/sync, backups, photos).
# See sovereignty/self-hosting/README.md for the full comparison and rollout order.
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
}
