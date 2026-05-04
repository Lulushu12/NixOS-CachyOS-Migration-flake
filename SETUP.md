# Detailed Setup Guide

## Pre-Installation

### What You'll Need
- NixOS installed (24.05 or unstable)
- Git (should be available on NixOS live)
- This flake repository
- Root/sudo access

### Backing Up Current System

Before switching to NixOS, back up important data:

```bash
# Example: Copy Documents, Pictures, Videos, Downloads
# Do this on your CachyOS system before wiping

mkdir -p ~/nixos-backup
cp -r ~/Documents ~/nixos-backup/
cp -r ~/Pictures ~/nixos-backup/
cp -r ~/Videos ~/nixos-backup/
cp -r ~/Downloads ~/nixos-backup/

# Backup SSH keys (be secure!)
cp -r ~/.ssh ~/nixos-backup/

# Backup important configs
cp ~/.zshrc ~/nixos-backup/
cp -r ~/.config/alacritty ~/nixos-backup/

# Backup gaming saves
cp -r ~/.steam ~/nixos-backup/
cp -r ~/Games ~/nixos-backup/
```

## Installation Steps

### Step 1: NixOS Installation

If you're doing a fresh NixOS install:

1. Boot the NixOS ISO
2. Follow the graphical installer
3. Choose ext4 filesystem (or your preferred)
4. Note your partition UUIDs during install
5. Finish installation and reboot

### Step 2: Get the Flake

```bash
# Option A: Clone from git (if you have repo access)
cd /etc/nixos
sudo git clone <repo-url> .

# Option B: Copy the directory
# Copy the entire "Claude Code - NixOS flake" folder to /etc/nixos
sudo cp -r "/home/radu/Downloads/Claude Code - NixOS flake"/* /etc/nixos/
```

### Step 3: Update hardware.nix

This is **critical** - without proper hardware configuration, your system won't boot!

#### Find Your Partition UUIDs:

```bash
# List all disks and partitions
lsblk

# Get detailed information with UUIDs
sudo blkid

# Example output:
# /dev/sda1: UUID="ABC123-EFG456" TYPE="vfat"
# /dev/sda2: UUID="XYZ789-QWE012" TYPE="ext4"
# /dev/sda3: UUID="DEF345-RTY678" TYPE="swap"
```

#### Edit hardware.nix:

```bash
sudo nano /etc/nixos/hosts/cachyos-to-nix/hardware.nix
```

Replace the UUID placeholders:

```nix
fileSystems."/" = {
  device = "/dev/disk/by-uuid/YOUR-ROOT-UUID";  # Your root (/) UUID from blkid
  fsType = "ext4";  # or whatever your filesystem is
};

fileSystems."/boot" = {
  device = "/dev/disk/by-uuid/YOUR-BOOT-UUID";  # Your /boot UUID
  fsType = "vfat";  # Usually vfat for EFI
};

swapDevices = [
  { device = "/dev/disk/by-uuid/YOUR-SWAP-UUID"; }  # Your swap UUID
];
```

### Step 4: Update networking.nix (Optional)

If you want to change the hostname from "CachyOS-Desktop":

```bash
sudo nano /etc/nixos/hosts/cachyos-to-nix/networking.nix
```

Change:
```nix
networking.hostName = "CachyOS-Desktop";  # Change to your preferred hostname
```

### Step 5: First Build

```bash
cd /etc/nixos

# Generate flake.lock (if it doesn't exist)
nix flake update

# Do the initial switch (this takes a while!)
sudo nixos-rebuild switch --flake .#cachyos-to-nix
```

**First build takes 30-60 minutes** depending on internet speed and disk speed.

### Step 6: Reboot

```bash
sudo reboot
```

After reboot, you should be at the SDDM login screen!

## First Boot

### At the SDDM Login Screen

1. Click on the "Session" dropdown (usually bottom-right corner)
2. Select either:
   - **Plasmawayland** - KDE Plasma (Wayland)
   - **Plasma** - KDE Plasma (Xorg, more stable)
   - **GNOME** - GNOME Desktop

3. Enter your password and log in
4. Wait for first startup (plasma may take a minute to initialize)

### First Login Checklist

- [ ] Desktop appears
- [ ] Taskbar/Dock works
- [ ] Applications menu opens
- [ ] Network connection works (check Wifi/Ethernet)
- [ ] Audio works (play a test sound)
- [ ] Try opening a terminal

### Set Up Your User

```bash
# Change git configuration
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Test git
git config --global --list

# Optional: Set up SSH keys
ssh-keygen -t ed25519 -C "your.email@example.com"
```

## Post-Installation

### 1. Restore Your Files

Copy back files from your backup:

```bash
# Example: Restore Documents, etc.
cp -r ~/nixos-backup/Documents ~
cp -r ~/nixos-backup/Pictures ~
cp -r ~/nixos-backup/Videos ~
cp -r ~/nixos-backup/Downloads ~

# Restore SSH keys (important: set correct permissions!)
cp -r ~/nixos-backup/.ssh ~
chmod 700 ~/.ssh
chmod 600 ~/.ssh/*
chmod 644 ~/.ssh/*.pub  # public keys only
```

### 2. Restore Steam/Games

```bash
# Steam is auto-started, but restore your games
cp -r ~/nixos-backup/.steam ~
cp -r ~/nixos-backup/Games ~
```

### 3. Test Each Desktop Environment

To ensure both work properly, test switching:

```bash
# Log off (Ctrl+Alt+Backspace or logout button)
# Try each DE:
# 1. KDE Plasma
# 2. GNOME

# Check they both work before customizing
```

### 4. Customize Your Setup

Now that the base system works, customize it:

#### Add Your Own Packages

Edit `home-manager/default.nix`:

```nix
home.packages = with pkgs; [
  # ... existing packages ...
  
  # Add your own:
  your-favorite-app
  another-tool
];
```

Apply changes:
```bash
home-manager switch --flake /etc/nixos#radu
```

#### Customize Your Shell Prompt

The flake comes with Powerlevel10k. To configure it:

```bash
# Run the configuration wizard
p10k configure

# Your settings save to ~/.config/zsh/.p10k.zsh
```

#### Set Default Applications

Edit `home-manager/modules/desktop/default.nix`:

```nix
xdg.mimeApps.defaultApplications = {
  "text/html" = "firefox.desktop";  # Change to your browser
  "application/pdf" = "org.kde.okular.desktop";  # Change to your PDF reader
  # etc.
};
```

### 5. Optimize Your System

```bash
# Clean up old packages
nix-collect-garbage -d

# Optimize store
nix-store --optimise

# Check your system
sudo systemd-analyze
sudo systemd-analyze critical-chain
```

## Testing Key Features

### Test Gaming Setup

```bash
# Test Steam installation
steam

# Test proton/wine games
cd ~/Games
# Try running a game

# Test performance monitoring
mangohud
gamemoderun wine game.exe
```

### Test Development Tools

```bash
# Test Python
python3 --version
pip --version

# Test Rust
rustc --version
cargo --version

# Test Node.js
node --version
npm --version

# Test Go
go version

# Test build tools
gcc --version
make --version
```

### Test GPU/Graphics

```bash
# Test NVIDIA drivers
nvidia-smi

# Test Vulkan
vulkaninfo

# Test OpenGL
glxinfo

# Test in a game (Steam has free games to test)
```

## Configuration After Setup

### Changing Shell Configuration

All shell config is in `home-manager/modules/shell/default.nix`.

To apply changes:
```bash
home-manager switch --flake /etc/nixos#radu
```

### Customizing Alacritty Terminal

The flake doesn't manage Alacritty by default. To enable it:

1. Edit `home-manager/modules/shell/default.nix`
2. Uncomment the alacritty section
3. Customize colors, fonts, etc.

### Installing Additional Programs

```bash
# Search for packages
nix search nixpkgs your-package

# Add to home.packages in home-manager/default.nix
# Or for system packages, add to modules/

# Apply changes
home-manager switch --flake /etc/nixos#radu
# OR for system changes:
sudo nixos-rebuild switch --flake /etc/nixos#cachyos-to-nix
```

## Troubleshooting

### Flake Won't Build

```bash
# Check for errors
nix flake check

# Update and try again
nix flake update

# Clean up
nix-collect-garbage -d
```

### NVIDIA Driver Issues

```bash
# Verify driver loaded
lsmod | grep nvidia

# Check for errors
dmesg | grep -i nvidia

# Try open drivers (edit hardware/nvidia.nix):
# hardware.nvidia.open = true;

sudo nixos-rebuild switch --flake /etc/nixos#cachyos-to-nix
```

### Can't Login

```bash
# Reboot to TTY if GUI hangs
# Ctrl+Alt+F2 to get TTY

# Check logs
journalctl -xe

# Rebuild with more info
sudo nixos-rebuild switch --flake /etc/nixos#cachyos-to-nix --show-trace
```

### Missing Permissions

```bash
# Some commands need sudo
sudo usermod -aG docker $USER
sudo usermod -aG wheel $USER

# Reboot to apply
sudo reboot
```

### Home-manager Conflicts

If you get file conflicts:

```bash
# Backup existing files
home-manager switch --flake /etc/nixos#radu --backup backup

# Or remove conflicting files first
rm ~/.config/file.conf
home-manager switch --flake /etc/nixos#radu
```

## Daily Usage

### Update System

```bash
# Update flake inputs
nix flake update --commit-lock-file

# Rebuild
sudo nixos-rebuild switch --flake /etc/nixos#cachyos-to-nix
```

### Update Home-manager Config

```bash
# Make changes to home-manager files
nano /etc/nixos/home-manager/...

# Apply
home-manager switch --flake /etc/nixos#radu
```

### Clean Up Storage

```bash
# Weekly cleanup (automatic, but manual run)
nix-collect-garbage -d

# Optimize store space
nix-store --optimise
```

## Next Steps

1. Read the main [README.md](README.md)
2. Customize modules to your liking
3. Add personal packages
4. Test all features
5. Set up backups (important!)
6. Enjoy your NixOS system!

---

Questions? Check NixOS wiki: https://nixos.wiki/
