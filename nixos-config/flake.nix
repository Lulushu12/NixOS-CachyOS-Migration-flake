{
  description = "Radu's NixOS system configuration";

  inputs = {
    # nixos-unstable — pinned for reproducibility. Prevents surprise rebuilds
    # when running `nix flake update`. To advance the pin:
    #   1. Check https://channels.nixos.org/nixos-unstable for the latest commit
    #   2. Update the hash below and delete flake.lock
    #   3. Run: sudo nix flake update /etc/nixos/nixos-config
    nixpkgs.url = "github:NixOS/nixpkgs/15f4ee454b1dce334612fa6843b3e05cf546efab";

    home-manager = {
      url = "github:nix-community/home-manager/fdb2ccba9d5e1238d32e0c4a3ec1a277efa80c1d";
      # Reuse the same nixpkgs as the system — avoids downloading a second copy.
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # Pinned to aaddrick fork which packages the current Claude Desktop version (1.6608.2).
    # k3d3/claude-desktop-linux-flake is stuck on 0.14.10 (too old, app rejects it).
    claude-desktop = {
      url = "github:aaddrick/claude-desktop-debian";
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
