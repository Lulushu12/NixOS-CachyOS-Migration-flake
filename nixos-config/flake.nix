{
  description = "Radu's NixOS system configuration";

  inputs = {
    # NixOS 25.05 stable — fully cached on cache.nixos.org so nothing builds
    # from source. Upgrade to nixos-unstable once you want Linux 7.x:
    #   https://channels.nixos.org/nixos-unstable  (grab the commit)
    #   delete flake.lock, run: sudo nix flake lock /etc/nixos/nixos-config
    nixpkgs.url = "github:NixOS/nixpkgs/ac62194c3917d5f474c1a844b6fd6da2db95077d";

    home-manager = {
      url = "github:nix-community/home-manager/44831a7eaba4360fb81f2acc5ea6de5fde90aaa3";
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
    # claude-desktop = {
    #   url = "github:k3d3/claude-desktop-linux-flake";
    #   inputs.nixpkgs.follows = "nixpkgs";
    # };
  };

  outputs = { self, nixpkgs, home-manager }@inputs:
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
