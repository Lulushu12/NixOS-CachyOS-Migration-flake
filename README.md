# Modular NixOS Flake - CachyOS to NixOS Migration

A complete, modular NixOS flake configuration designed to act as a **unified monorepo** for both your high-end Desktop (CachyOS migration) and your Lenovo Laptop. It manages both **KDE Plasma** and **GNOME** target systems side-by-side using a DRY modular architecture.

## Structure

```
.
├── flake.nix                           # Main entry point
├── hosts/                                # Machine-specific profiles
│   ├── cachyos-to-nix/                 # High-end Desktop (NVIDIA)
│   │   ├── default.nix                 
│   │   └── hardware.nix                
│   └── laptop-personal/                # Lenovo IdeaPad (AMD Hybrid + TLP battery profile)
│       ├── default.nix
│       ├── hardware.nix
│       └── networking.nix
├── modules/                            # Reusable NixOS modules
│   ├── desktop/
│   │   ├── kde.nix                     # KDE Plasma 6 configuration
│   │   └── gnome.nix                   # GNOME configuration (installed together)
│   ├── hardware/
│   │   └── nvidia.nix                  # NVIDIA RTX 2070 SUPER drivers
│   ├── gaming/
│   │   └── gaming.nix                  # Steam, Lutris, Proton, Wine
│   ├── development/
│   │   └── dev-tools.nix               # Build tools, IDEs, compilers
│   ├── system/
│   │   ├── boot.nix                    # Boot configuration
│   │   ├── services.nix                # System services (CUPS, NetworkManager, etc.)
│   │   └── localization.nix            # Locale, timezone, keyboard
│   └── shell/
│       └── shell-config.nix            # Zsh, bash, shell utilities
└── home-manager/                       # User-level configuration
    ├── default.nix                     # Main home-manager config
    └── modules/
        ├── shell/
        │   └── default.nix             # Zsh with Powerlevel10k, git, direnv
        ├── desktop/
        │   ├── default.nix             # Common desktop settings (XDG, GTK, Qt)
        │   ├── kde.nix                 # KDE-specific home-manager config
        │   └── gnome.nix               # GNOME-specific home-manager config
        ├── development/
        │   └── default.nix             # Dev tools, language servers, IDEs
        ├── media/
        │   └── default.nix             # Media software (GIMP, Blender, video editors)
        └── gaming/
            └── default.nix             # Gaming configs (Steam, Lutris, MangoHUD)
```

## Features

### 🎨 Dual Desktop Environment Support
- **Both KDE Plasma 6 and GNOME** installed simultaneously
- Switch between them at SDDM login screen
- No rebuild needed to switch
- Session persistence across DE switches

### 🎮 Gaming Ready
- NVIDIA RTX 2070 SUPER with proprietary drivers
- Steam, Lutris, and Proton GE support
- MangoHUD for performance monitoring
- GameMode for optimal performance
- 32-bit libraries for legacy game support

### 👨‍💻 Development Ready
- 317+ development packages (mirrors your CachyOS setup)
- Support for Python, Rust, Go, Node.js, C/C++
- IDEs: VS Code, JetBrains community, Sublime
- Language servers and formatters
- Docker, git, build tools, debuggers

### 🔧 Modular Architecture
- Each module can be easily enabled/disabled
- Swap components without affecting others
- Easy to extend with new modules
- Clear separation of concerns

### 🎵 Media & Creative Suite
- GIMP, Blender, Inkscape, Krita
- KDenlive, OBS Studio
- Audacity, Ardour (DAW)
- FFmpeg, ImageMagick
- Calibre for ebook management

## Quick Start

### Prerequisites
- NixOS installed (or use NixOS ISO)
- Git installed
- This flake on your system

### Installation

1. **Clone or copy this flake to your NixOS system:**
```bash
cd /etc/nixos
sudo git clone <your-repo-url> .
# Or copy the entire directory
```

2. **Update hardware.nix with your actual configuration:**
   - Get your UUIDs: `blkid`
   - Update `/dev/disk/by-uuid/YOUR-*-UUID` entries
   - Adjust boot loader if needed

3. **Build and activate the configuration:**
   - For your Desktop:
```bash
sudo nixos-rebuild switch --flake .#cachyos-to-nix
```
   - For your Laptop:
```bash
sudo nixos-rebuild switch --flake .#laptop-personal
```

4. **Reboot and enjoy!**
```bash
sudo reboot
```

At the SDDM login screen, click the session dropdown to choose between **KDE Plasma** or **GNOME**.

## Customization

### Enabling/Disabling Features

Edit `hosts/cachyos-to-nix/default.nix` to remove imports you don't need:

```nix
imports = [
  ./hardware.nix
  ./networking.nix
  ../../modules/system/boot.nix
  # ../../modules/gaming/gaming.nix  # Uncomment to skip gaming
  # ../../modules/development/dev-tools.nix  # Uncomment to skip dev tools
];
```

### Changing Desktop Environment

Both are installed by default. To remove GNOME or KDE:

**Remove GNOME:**
```nix
# In hosts/cachyos-to-nix/default.nix, remove or comment:
# ../../modules/desktop/gnome.nix
```

**Remove KDE:**
```nix
# In hosts/cachyos-to-nix/default.nix, remove or comment:
# ../../modules/desktop/kde.nix
```

### Adding Personal Packages

Edit `home-manager/default.nix` under `home.packages`:

```nix
home.packages = with pkgs; [
  your-package-here
  another-package
];
```

### Modifying Shell Configuration

Edit `home-manager/modules/shell/default.nix` to customize:
- Powerlevel10k prompt
- Aliases
- Shell plugins
- Git configuration

### Updating Flake Inputs

```bash
nix flake update
sudo nixos-rebuild switch --flake .#cachyos-to-nix
```

## Important Configuration Files

### hardware.nix
**Must be updated with your actual hardware!**
- Block device UUIDs
- Boot loader configuration
- CPU microcode settings
- Filesystem mounts

Get your UUIDs:
```bash
sudo blkid
lsblk
```

### networking.nix
- Hostname (currently "CachyOS-Desktop")
- NetworkManager configuration
- Firewall rules
- SSH settings

### modules/hardware/nvidia.nix
- NVIDIA driver version
- CUDA toolkit support
- Power management settings

## Troubleshooting

### Switch between KDE and GNOME
1. Log off your current session
2. On the SDDM login screen, click the session dropdown (usually bottom-right)
3. Select "Plasmawayland" (KDE) or "GNOME" (or "GNOME on Xorg")
4. Log back in

### NVIDIA Driver Issues
If you encounter graphical issues:

```bash
# Verify driver installation
nvidia-smi

# Check dmesg for errors
sudo dmesg | grep -i nvidia

# Fallback to open drivers (if needed)
# Edit modules/hardware/nvidia.nix:
# hardware.nvidia.open = true;
```

### Flake Lock Issues
If you get lock file warnings:

```bash
nix flake update --commit-lock-file
```

### Home-manager Conflicts
If home-manager reports conflicts:

```bash
home-manager switch --flake .#radu
# or
home-manager switch --flake . --backup backup-$(date +%s)
```

## Performance Tips

1. **Enable GameMode** for gaming (automatic via the module)
2. **Use MangoHUD** for FPS and performance monitoring
3. **Set appropriate kernel scheduler**: Already optimized in boot.nix
4. **Monitor with btop**: `btop` in terminal
5. **Check GPU usage**: `nvidia-smi -l 1` for live stats

## System Maintenance

### Garbage Collection
Runs automatically weekly. Manual cleanup:
```bash
nix-collect-garbage -d
nix-store --gc
```

### Optimizing Store
Automatic in the flake. Manual:
```bash
nix-store --optimise
```

### Checking System Health
```bash
sudo systemctl status
journalctl -xe
sudo smartctl -a /dev/sda
```

## File Backups from Original System

If you want to preserve configurations from your CachyOS installation, manually copy:

- `.config/` - Application configurations
- `.local/share/` - Application data
- `.zshrc`, `.bashrc` - Shell configs (or merge with our setup)
- `.ssh/` - SSH keys (be careful with permissions!)
- `.gnupg/` - GPG keys

After copying, don't forget to set proper permissions:
```bash
chmod 700 ~/.ssh
chmod 700 ~/.gnupg
```

## Important Notes

1. **State Version**: Set to "24.05" - only change when upgrading NixOS releases
2. **Unfree Packages**: `nixpkgs.config.allowUnfree = true` enabled in flake
3. **Experimental Features**: None required; uses stable Nix CLI
4. **NixOS Unstable**: Uses nixos-unstable for latest packages

## Adding More Modules

To add a new module (e.g., for a specific application):

1. Create `modules/category/your-module.nix`:
```nix
{ config, pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    # Your packages here
  ];

  # Your configuration here
}
```

2. Import it in `hosts/cachyos-to-nix/default.nix`:
```nix
imports = [
  # ... existing imports
  ../../modules/category/your-module.nix
];
```

## Contributing

Feel free to customize this flake to your needs. If you find improvements, document them for future reference.

## License

This configuration is provided as-is. Customize as needed for your system.

---

**Happy NixOS-ing!** 🐧
