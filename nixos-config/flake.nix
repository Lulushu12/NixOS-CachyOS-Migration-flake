{
  description = "Radu's NixOS system configuration";

  inputs = {
    # nixos-unstable — rolling release with Linux 7.x and NVIDIA 595.
    # Run `sudo nix flake update /etc/nixos/nixos-config` to advance the pin.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    home-manager = {
      url = "github:nix-community/home-manager";
      # Reuse the same nixpkgs as the system — avoids downloading a second copy.
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # Claude Desktop — DISABLED: k3d3/claude-desktop-linux-flake uses
    # nodePackages.asar which was removed from nixpkgs on 2026-03-03.
    # Re-enable once https://github.com/k3d3/claude-desktop-linux-flake/pull/89 merges.
    # claude-desktop = {
    #   url = "github:k3d3/claude-desktop-linux-flake";
    #   inputs.nixpkgs.follows = "nixpkgs";
    # };
  };

  outputs = { self, nixpkgs, home-manager, ... }@inputs:
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
