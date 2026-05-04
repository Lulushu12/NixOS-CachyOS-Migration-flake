# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A **modular NixOS flake configuration** for a personal system (CachyOS migration target). Features dual desktop environments (KDE Plasma & GNOME), gaming setup with NVIDIA RTX 2070 SUPER, and 317+ development packages. The flake is organized into reusable system modules, hardware-specific configs, and home-manager configurations for user-level customization.

- **Main entry**: `flake.nix` (defines nixpkgs/home-manager inputs and outputs)
- **Host config**: `hosts/cachyos-to-nix/` (applies all modules, hardware, networking)
- **System modules**: `modules/` (self-contained subsystem configs: desktop, gaming, dev-tools, etc.)
- **User config**: `home-manager/` (user-level packages, dotfiles, per-app settings)

## Essential Commands

### System Rebuilding (Most Common)

```bash
# Apply changes and activate immediately
sudo nixos-rebuild switch --flake /etc/nixos#cachyos-to-nix

# From /etc/nixos directory (shorter):
cd /etc/nixos && sudo nixos-rebuild switch --flake .#cachyos-to-nix

# Test changes without activating
sudo nixos-rebuild test --flake .#cachyos-to-nix

# Rollback to previous generation
sudo nixos-rebuild switch --rollback
```

### Home-Manager (User-Level Config)

```bash
# Apply user-level changes
home-manager switch --flake /etc/nixos#radu

# From /etc/nixos:
home-manager switch --flake .#radu
```

### Flake Updates & Maintenance

```bash
# Update all inputs to latest versions
nix flake update

# Update specific input (e.g., nixpkgs)
nix flake update nixpkgs

# Check flake syntax/validity
nix flake check

# Show available configurations
nix flake show
```

### Cleanup & Optimization

```bash
# Remove unused packages (safe)
nix-collect-garbage -d

# Aggressive cleanup with store optimization
nix-collect-garbage -d && nix-store --optimise
```

## Code Architecture

### Directory Structure

```
flake.nix                          # Entry point: declares inputs, outputs, host config
├── hosts/cachyos-to-nix/
│   ├── default.nix               # Host configuration: imports all modules
│   ├── hardware.nix              # Storage, boot, CPU microcode (MUST BE UPDATED)
│   └── networking.nix            # Hostname, firewall, SSH
│
├── modules/                       # System-level modules (reusable)
│   ├── system/
│   │   ├── boot.nix              # Bootloader, kernel, GRUB/systemd-boot
│   │   ├── localization.nix      # Timezone, locale, keyboard, fonts
│   │   └── services.nix          # PipeWire, Bluetooth, CUPS, Docker, UDisks2, etc.
│   ├── hardware/
│   │   └── nvidia.nix            # NVIDIA drivers, CUDA, power management
│   ├── desktop/
│   │   ├── kde.nix               # KDE Plasma 6 (display-server, packages)
│   │   └── gnome.nix             # GNOME desktop (sessionVariables, packages)
│   ├── gaming/
│   │   └── gaming.nix            # Steam, Lutris, Proton, Wine, MangoHUD, 32-bit libs
│   ├── development/
│   │   └── dev-tools.nix         # Compilers, build tools, IDEs, language servers
│   └── shell/
│       └── shell-config.nix      # System-wide shell settings (NixOS-managed)
│
└── home-manager/                  # User-level configuration (per-user dotfiles & packages)
    ├── default.nix               # Main home-manager config, global packages
    └── modules/
        ├── shell/                # Zsh, Powerlevel10k, aliases, git config
        ├── desktop/              # XDG dirs, GTK/Qt theming, KDE/GNOME specifics
        ├── development/          # User dev tools, language runtimes, formatters
        ├── media/                # GIMP, Blender, Krita, KDenlive, Audacity
        └── gaming/               # MangoHUD config, game-specific settings
```

### Configuration Flow

1. **`flake.nix`** declares inputs (nixpkgs-unstable, home-manager) and outputs a nixosConfiguration named `cachyos-to-nix`
2. **`hosts/cachyos-to-nix/default.nix`** (referenced in flake) imports all modules and sets `system.stateVersion`
3. **System modules** (`modules/*/`) configure system-wide services, packages, and settings
4. **Home-manager** (integrated in flake) manages user-level configs, dotfiles, and per-app settings
5. **Rebuild** compiles everything into `/nix/store`, symlinks to `/run/current-system`, and activates

### Key Design Patterns

- **Module isolation**: Each system module is self-contained (e.g., `modules/gaming/gaming.nix` has all gaming packages/config in one file)
- **Dual DE support**: Both KDE and GNOME modules are imported; user switches at SDDM login without rebuild
- **Hardware abstraction**: `hardware.nix` is separated from `default.nix` to allow easy hardware-specific customization
- **Home-manager integration**: Home-manager config is defined in `flake.nix` and points to `home-manager/` directory
- **Unfree packages**: `nixpkgs.config.allowUnfree = true` in host config allows proprietary software (drivers, Steam, etc.)

## Important Files

### Must-Update Files

- **`hosts/cachyos-to-nix/hardware.nix`**: Must match actual hardware (UUIDs, boot partition, CPU type). Run `blkid` and `lsblk` to find values.
- **`hosts/cachyos-to-nix/networking.nix`**: Hostname ("CachyOS-Desktop" by default), firewall rules, SSH config.

### Commonly Modified Files

- **Add system packages**: Add to `environment.systemPackages` in appropriate module file (e.g., `modules/development/dev-tools.nix`)
- **Add user packages**: Add to `home.packages` in `home-manager/default.nix` or related module
- **Change desktop environment**: Edit `hosts/cachyos-to-nix/default.nix` imports (comment out `kde.nix` or `gnome.nix`)
- **Customize shell**: Edit `home-manager/modules/shell/default.nix` (Zsh config, aliases, git)

## Common Tasks

### Adding a System Package

1. Identify which module it belongs to (e.g., if it's a game, use `modules/gaming/gaming.nix`)
2. Edit the module and add package name to `environment.systemPackages` list
3. Rebuild: `sudo nixos-rebuild switch --flake .#cachyos-to-nix`

### Adding a User-Level Package

1. Edit `home-manager/default.nix` or relevant module in `home-manager/modules/`
2. Add package name to `home.packages` list
3. Apply: `home-manager switch --flake /etc/nixos#radu`

### Enabling/Disabling a Feature

Edit `hosts/cachyos-to-nix/default.nix` imports:
- **Comment out** to disable: `# ../../modules/gaming/gaming.nix`
- **Uncomment** to enable: `../../modules/gaming/gaming.nix`
- Rebuild after changes

### Switching Between KDE and GNOME

Both are installed. At SDDM login screen, click session dropdown (bottom-right), select "Plasmawayland" (KDE) or "GNOME", then log in. **No rebuild needed.**

## Reference Files

- **README.md**: Full feature overview and installation guide
- **QUICK-REFERENCE.md**: Comprehensive command cheat sheet (system, package, desktop, gaming, shell, config)
- **MODULES.md**: Detailed module documentation with customization examples
- **SETUP.md**: Step-by-step initial installation guide
- **TROUBLESHOOTING.md**: Diagnosis and fixing common issues

## Development Notes

### Module Creation Pattern

When adding a new module (e.g., `modules/category/newmodule.nix`):

```nix
{ config, pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    # Packages here
  ];
  
  # Configuration here
  # services.yourservice.enable = true;
  # etc.
}
```

Then import it in `hosts/cachyos-to-nix/default.nix`:

```nix
imports = [
  # ... existing
  ../../modules/category/newmodule.nix
];
```

### Testing Changes

- Use `sudo nixos-rebuild test --flake .#cachyos-to-nix` to test without persisting (reverts after reboot)
- Use `sudo nixos-rebuild build --flake .#cachyos-to-nix` to build but not activate
- Use rollback if something breaks: `sudo nixos-rebuild switch --rollback`

### Debugging Build Issues

```bash
# Show detailed error messages
sudo nixos-rebuild switch --flake .#cachyos-to-nix --show-trace

# Check flake syntax
nix flake check

# Validate expressions
nix eval .
```

## Key Behaviors

- **State version**: Set to "24.05" in `hosts/cachyos-to-nix/default.nix`. Change only when upgrading NixOS releases.
- **Auto-optimization**: Nix store automatically optimizes on rebuild (`auto-optimise-store = true`)
- **Unfree packages enabled**: NVIDIA drivers, Steam, and other proprietary software work without additional config
- **Home-manager backups**: Files are backed up with `.backup` extension on conflicts during switch
- **Generations**: Both system and home-manager maintain rollback points (accessible via `nix-env --switch-generation`)

## Performance & Gaming

- NVIDIA RTX 2070 SUPER with proprietary drivers (configured in `modules/hardware/nvidia.nix`)
- MangoHUD and GameMode enabled in `modules/gaming/gaming.nix` for performance monitoring
- Steam and Proton GE configured for game compatibility
- 32-bit libraries included for legacy games
