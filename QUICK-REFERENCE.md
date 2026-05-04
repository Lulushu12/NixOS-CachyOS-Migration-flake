# Quick Reference Guide

Fast commands and common operations for your NixOS flake setup.

## System Management

### Rebuilding Your System

```bash
# Apply all changes (system + home-manager)
sudo nixos-rebuild switch --flake /etc/nixos#cachyos-to-nix

# Test changes without applying
sudo nixos-rebuild test --flake /etc/nixos#cachyos-to-nix

# Build to install later
sudo nixos-rebuild build --flake /etc/nixos#cachyos-to-nix

# Rollback to previous generation
sudo nixos-rebuild switch --rollback

# List all generations
nix profile history
```

### Home-Manager

```bash
# Apply home-manager changes
home-manager switch --flake /etc/nixos#radu

# Test home-manager changes
home-manager news

# Check current home-manager config
home-manager option

# List generations
home-manager generations
```

### Updating

```bash
# Update all flake inputs
nix flake update

# Update specific input
nix flake update nixpkgs

# Update and commit to git
nix flake update --commit-lock-file

# Rebuild after updating
sudo nixos-rebuild switch --flake /etc/nixos#cachyos-to-nix
```

## System Maintenance

### Garbage Collection

```bash
# Remove unused packages (safe)
nix-collect-garbage -d

# Aggressive cleaning
nix-collect-garbage -d && nix-store --optimise

# Check what will be deleted (dry run)
nix-collect-garbage --dry-run

# Delete old generations
sudo nix-collect-garbage -d --delete-old
```

### Storage Info

```bash
# Check store usage
du -sh /nix/store

# Check home cache
du -sh ~/.cache

# Find largest packages
nix path-info -S /run/current-system | head -20

# Check disk space
df -h
```

### Performance

```bash
# System analysis
systemd-analyze

# Boot time breakdown
systemd-analyze blame

# Check running services
systemctl status

# Monitor system
btop

# Check GPU usage
watch -n 1 nvidia-smi

# Check processes
ps aux --sort=-%cpu | head -10
```

## Desktop Environment

### Switching Between KDE and GNOME

```bash
# At SDDM login screen:
# 1. Click "Session" dropdown (bottom right)
# 2. Select "Plasmawayland" (KDE) or "GNOME"
# 3. Click "Sign In"

# Command line to log off gracefully
loginctl terminate-user $USER

# Force exit if needed
pkill -9 kwin_wayland  # For KDE Wayland
pkill -9 mutter        # For GNOME
```

### KDE Plasma

```bash
# Restart Plasma
kquitapp5 plasmashell && plasmashell &
# or
systemctl --user restart plasmacompositor

# Reconfigure KDE
kq-restart

# Open system settings
systemsettings6

# Configure Powerlevel10k prompt
p10k configure
```

### GNOME

```bash
# Restart GNOME Shell
systemctl --user restart gnome-shell

# Open settings
gnome-control-center

# Enable/reload extensions
dconf reset -f /

# Install extension from command line
gnome-extensions install extension-name
```

## Package Management

### Installing/Removing Packages

```bash
# Search for a package
nix search nixpkgs name

# Show package details
nix show-derivation nixpkgs#package-name

# Install temporarily
nix run nixpkgs#package-name

# Install shell with package
nix shell nixpkgs#package-name

# Install via flake
nix profile install github:nixos/nixpkgs#package-name

# Show installed packages
nix profile list
```

### Finding Packages

```bash
# Search by name
nix search nixpkgs 'firefox'

# Search by regex
nix search nixpkgs '^rust'

# Show package info
nix show-config

# Check dependencies
nix why-depends /run/current-system package

# Find binary
which steam
type nvim
```

## Development

### Dev Environments

```bash
# Create dev environment
nix develop

# Load direnv automatically
echo 'use flake' > .envrc
direnv allow

# Exit dev environment
exit

# Create project flake template
nix flake new my-project -t github:nixos/templates#rust
```

### Language-Specific

```bash
# Python
nix develop
python --version

# Rust
cargo new project
rustup default stable

# Node
npm init
pnpm install

# Go
go mod init
go version
```

### Building/Testing

```bash
# Build current flake
nix build

# Run tests
nix flake check

# Lint Nix files
nix flake show

# Format Nix files
nixfmt *.nix
```

## Gaming

### Steam

```bash
# Launch Steam
steam

# Run game with MangoHUD
MANGOHUD=1 steam

# Run game with verbose output
PROTON_LOG=1 steam run game.exe

# Check Proton version
proton --version

# View installed games
protontricks list-installed
```

### Lutris

```bash
# Launch Lutris
lutris

# Install game from command line
lutris 'lutris:https://lutris.net/games/game-name/'

# Show game info
lutris --list-games
```

### Emulation

```bash
# Dolphin (GameCube/Wii)
dolphin-emu-primehack

# PCSX2 (PS2)
pcsx2

# mGBA (Game Boy)
mgba
```

## Shell & Terminal

### Common Commands

```bash
# Update shell config
source ~/.zshrc

# Edit shell config
nano ~/.config/zsh/.zshenv

# List available shells
cat /etc/shells

# Change default shell
chsh -s /run/current-system/sw/bin/zsh

# Reload shell plugins
exec zsh
```

### Useful Aliases

```bash
# Already configured:
ll          # ls -lah
la          # ls -la
cls         # clear
gs          # git status
ga          # git add
gc          # git commit
gp          # git push
gl          # git log

# Create custom alias
alias myalias='command'

# Add to ~/.config/zsh/.zshrc and reload
```

### Powerlevel10k

```bash
# Configure prompt
p10k configure

# Show transient prompt
p10k transient

# Right-click menu (Alacritty)
# Right-click → Color Scheme
```

## Configuration

### Editing System Config

```bash
# Main system config
sudo nano /etc/nixos/hosts/cachyos-to-nix/default.nix

# Desktop environment
sudo nano /etc/nixos/modules/desktop/kde.nix
sudo nano /etc/nixos/modules/desktop/gnome.nix

# Hardware
sudo nano /etc/nixos/hosts/cachyos-to-nix/hardware.nix

# Services
sudo nano /etc/nixos/modules/system/services.nix
```

### Editing User Config

```bash
# Home-manager config
nano /etc/nixos/home-manager/default.nix

# Shell config
nano /etc/nixos/home-manager/modules/shell/default.nix

# Desktop config
nano /etc/nixos/home-manager/modules/desktop/default.nix

# Custom configs
nano ~/.config/yourapp/config.file
```

### Applying Changes

```bash
# System-level changes
sudo nixos-rebuild switch --flake /etc/nixos#cachyos-to-nix

# User-level changes
home-manager switch --flake /etc/nixos#radu

# Both (from /etc/nixos):
sudo nixos-rebuild switch --flake .#cachyos-to-nix
```

## Troubleshooting Commands

### Diagnostics

```bash
# System logs
journalctl -xe

# Kernel messages
dmesg | tail -50

# Last boot issues
journalctl -b -1

# Specific service
journalctl -u sddm -f

# High memory usage
ps aux --sort=-%mem | head

# High CPU usage
ps aux --sort=-%cpu | head

# Disk usage
du -sh ~/ | sort -h

# Network status
ip addr
ip route
```

### Fixing Issues

```bash
# Check flake syntax
nix flake check

# Validate all modules
nix eval .

# Force rebuild everything
sudo nixos-rebuild switch --flake .#cachyos-to-nix --show-trace

# Check specific module
nix eval .#modules.desktop.kde

# Hard reset Plasma cache
rm -rf ~/.cache/kde*
rm -rf ~/.local/share/kxmlgui5

# Hard reset GNOME cache
rm -rf ~/.cache/gnome-shell
rm -rf ~/.local/share/evolution
```

## Useful Tools

### System Info

```bash
# Full system info
fastfetch
neofetch

# CPU info
lscpu

# GPU info
nvidia-smi
glxinfo

# RAM info
free -h

# Disk info
lsblk
df -h

# Network info
ip addr
nmcli device
```

### File Management

```bash
# Search files
fd filename
find . -name pattern

# Search file contents
rg "pattern"
grep -r "pattern"

# Disk usage
du -sh directory
ncdu

# File diff
diff file1 file2
delta file1 file2

# Archive
tar -czf archive.tar.gz directory
unzip file.zip
```

### Development Tools

```bash
# Git
git status
git log --oneline
git diff

# Debugging
gdb program
lldb program

# Performance
time command
perf record command

# Testing
pytest
cargo test
npm test

# Linting
flake8
cargo check
```

## File Locations

### Important Paths

```bash
# System configuration
/etc/nixos/

# Home configuration
~/.config/
~/.local/

# NixOS store
/nix/store/

# System generation
/run/current-system/

# Boot files
/boot/efi/

# Logs
~/.local/share/sddm/
/var/log/

# Flake lock
/etc/nixos/flake.lock
```

### Config Directories

```bash
# Zsh
~/.config/zsh/

# KDE Plasma
~/.config/plasmashellrc
~/.config/kwinrc

# GNOME
~/.config/dconf/

# Alacritty
~/.config/alacritty/

# Git
~/.config/git/
~/.gitconfig

# SSH
~/.ssh/

# NVIDIA
~/.nvidia/
```

## Common Tasks

### Add a New Package

1. Edit appropriate file:
   - System: `modules/*/module.nix`
   - User: `home-manager/default.nix` or `home-manager/modules/*/default.nix`

2. Add package name to `environment.systemPackages` or `home.packages`

3. Apply:
```bash
sudo nixos-rebuild switch --flake .#cachyos-to-nix
# or
home-manager switch --flake /etc/nixos#radu
```

### Enable a Feature

1. Find relevant module in `modules/`

2. Edit and uncomment/enable feature

3. Rebuild:
```bash
sudo nixos-rebuild switch --flake .#cachyos-to-nix
```

### Change Desktop Environment

1. At SDDM login, click "Session"
2. Choose "Plasmawayland" or "GNOME"
3. Log in

### Create Custom Module

1. Create file: `modules/custom/yourmodule.nix`

2. Edit `hosts/cachyos-to-nix/default.nix`:
```nix
imports = [
  # ... other imports
  ../../modules/custom/yourmodule.nix
];
```

3. Rebuild:
```bash
sudo nixos-rebuild switch --flake .#cachyos-to-nix
```

## Tips & Tricks

```bash
# Keep recent generations only (saves space)
nix-collect-garbage -d

# Monitor rebuild progress
watch -n 1 'ls /nix/store | wc -l'

# Count installed packages
nix eval --raw 'builtins.length (builtins.attrValues (import <nixpkgs> {}).buildPackages)' 2>/dev/null

# Find package version
nix eval -f '<nixpkgs>' -A firefox.version --raw

# Replay logs in real-time
sudo journalctl -f -u sddm

# Create quick dev shell
nix run nixpkgs#vim -- file.txt

# Check what changed
git diff /etc/nixos/
```

## Emergency Commands

```bash
# Boot into previous generation
# At GRUB menu, select previous generation
# Or via command line:
sudo nix-env --switch-generation <generation-number>

# Rescue mode
# At GRUB, press 'e' to edit, add 'rd.break' to kernel line
# Then: mount -o remount,rw /
# Fix your system
# Then: exit

# Force shutdown (emergency)
sudo shutdown -h now

# Restart (emergency)
sudo reboot --force
```

---

**Pro Tip**: Keep this file bookmarked! Copy commands as needed.

For more detailed information, see:
- **README.md** - Overview and features
- **SETUP.md** - Initial installation
- **MODULES.md** - Module documentation
- **TROUBLESHOOTING.md** - Problem solving
