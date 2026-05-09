{
  description = "Radu's NixOS system configuration";

  inputs = {
    # nixos-unstable — pinned for reproducibility. Provides Linux 7.x via
    # linuxPackages_latest (not available in the frozen 25.05 stable channel).
    # To update: grab the new commit from https://channels.nixos.org/nixos-unstable,
    # delete flake.lock, then run: sudo nix flake lock /etc/nixos/nixos-config
    nixpkgs.url = "github:NixOS/nixpkgs/15f4ee454b1dce334612fa6843b3e05cf546efab";

    home-manager = {
      url = "github:nix-community/home-manager/9c6f1307e1d76a2285d8001e1b8bc281bfe15dac";
      # Reuse the same nixpkgs as the system — avoids downloading a second copy.
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # Claude Desktop — not in nixpkgs, maintained as a community flake.
    # DISABLED for initial install: the flake input is unlocked and nix cannot
    # write the lock file when installing via git+file://.
    # To re-enable after first boot:
    #   1. Uncomment the block below
    #   2. Uncomment ../../modules/claude.nix in hosts/nixos/default.nix
    #   3. Run: sudo nix flake update && sudo nixos-rebuild switch --flake /etc/nixos#nixos
    # Pinned to PR #89 branch (fix: replace nodePackages.asar with buildNpmPackage)
    # because the main branch is broken on nixpkgs-unstable post-2026-03-03.
    # Switch back to "github:k3d3/claude-desktop-linux-flake" once PR #89 is merged.
    claude-desktop = {
      url = "github:naotoo1/claude-desktop-linux-flake/fix/remove-nodepackages-asar";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, home-manager, claude-desktop, ... }@inputs:
  let
    nixosSystem = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      # Pass all flake inputs to every module via specialArgs.
      # Modules that need a flake input (e.g. claude.nix) receive it as a parameter.
      specialArgs = { inherit inputs; };
      modules = [
        # ── System configuration ────────────────────────────────────────────
        ./hosts/nixos/default.nix

        # ── Home Manager (manages user-level config alongside system) ───────
        home-manager.nixosModules.home-manager
        {
          # Share system nixpkgs — no duplicate downloads
          home-manager.useGlobalPkgs = true;
          # Install user packages to /etc/profiles instead of ~/.nix-profile
          home-manager.useUserPackages = true;
          # Back up any dotfiles that conflict instead of failing
          home-manager.backupFileExtension = "backup";

          home-manager.users.radu = import ./home/radu.nix;
        }
      ];
    };
  in
  {
    nixosConfigurations = {
      nixos = nixosSystem;
      # Alias for CI systems that append --no-write-lock-file to the hostname
      "nixos--no-write-lock-file" = nixosSystem;
    };
  };
}
