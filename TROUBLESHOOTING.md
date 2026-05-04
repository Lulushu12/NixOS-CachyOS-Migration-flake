# Troubleshooting Guide

## Desktop Environment Issues

### Can't Switch Between KDE and GNOME

**Problem**: Desktop environment selection not appearing at login screen.

**Solutions**:

```bash
# Ensure both DEs are enabled in the flake
# Check hosts/cachyos-to-nix/default.nix includes both:
# ../../modules/desktop/kde.nix
# ../../modules/desktop/gnome.nix

# Check SDDM is configured correctly
sudo systemctl status sddm

# Try restarting SDDM
sudo systemctl restart sddm

# Check available sessions
ls -la /usr/share/wayland-sessions/
ls -la /usr/share/xsessions/
```

### KDE Plasma Won't Start

**Problem**: Black screen or crash on KDE login.

**Solutions**:

```bash
# Check for corruption
sudo rm -rf ~/.cache/kde*
sudo rm -rf ~/.local/share/kxmlgui5

# Try Plasma on Xorg instead of Wayland
# At SDDM, select "Plasma (X11)" instead of "Plasmawayland"

# Check logs
journalctl -xe
dmesg | tail -20

# Rebuild with more debug info
sudo nixos-rebuild switch --flake .#cachyos-to-nix --show-trace

# If still broken, temporarily remove KDE:
# In hosts/cachyos-to-nix/default.nix, comment:
# ../../modules/desktop/kde.nix
# Then rebuild and try GNOME
```

### GNOME Won't Start

**Problem**: Black screen, slow startup, or extensions not loading.

**Solutions**:

```bash
# Clear GNOME cache
sudo rm -rf ~/.cache/gnome-shell
sudo rm -rf ~/.local/share/evolution

# Reset GNOME settings
dconf reset -f /

# Try rebuilding
sudo nixos-rebuild switch --flake .#cachyos-to-nix

# Check extension compatibility
# Edit home-manager/modules/desktop/gnome.nix
# Comment out problematic extensions:
# "appindicatorSupport@rgcjonas.gmail.com"

# View GNOME logs
journalctl -u gnome-shell -f
```

---

## NVIDIA Graphics Issues

### No Graphics / Black Screen After Boot

**Problem**: System boots but no display output.

**Solutions**:

```bash
# Check if driver loaded
lsmod | grep nvidia

# View error messages
dmesg | grep -i nvidia
dmesg | grep -i gpu

# Try safe graphics mode
# Edit modules/hardware/nvidia.nix:
# hardware.nvidia.open = true;  # Use open drivers temporarily

# Rebuild
sudo nixos-rebuild switch --flake .#cachyos-to-nix

# Check driver version
nvidia-smi

# If still broken, try Xorg instead of Wayland
# At SDDM, select "(X11)" instead of "Wayland"
```

### NVIDIA Driver Mismatch

**Problem**: `nvidia-smi` shows mismatched versions.

**Solutions**:

```bash
# Update flake
nix flake update

# Rebuild with new drivers
sudo nixos-rebuild switch --flake .#cachyos-to-nix

# If compilation fails:
# Check available NVIDIA versions
nix search nixpkgs nvidia-driver

# Pin specific version in modules/hardware/nvidia.nix
```

### Game/Application Shows No GPU

**Problem**: `glxinfo` or game says no GPU found.

**Solutions**:

```bash
# Test GL
glxinfo | grep "OpenGL renderer"

# Test Vulkan
vulkaninfo

# Check 32-bit support
glxinfo | grep "OpenGL version"

# Ensure 32-bit libs in hardware/nvidia.nix:
hardware.graphics.enable32Bit = true;

# Rebuild
sudo nixos-rebuild switch --flake .#cachyos-to-nix
```

---

## System Won't Boot

### Can't Find Root Filesystem

**Problem**: Boot fails with "no such device" or UUID not found.

**Solutions**:

```bash
# Boot from ISO or recovery shell
# Check actual UUIDs:
blkid

# Update hosts/cachyos-to-nix/hardware.nix with CORRECT UUIDs

# Rebuild from recovery shell
# Mount your /
sudo mount /dev/sda2 /mnt

# Mount boot
sudo mount /dev/sda1 /mnt/boot

# Reinstall bootloader
sudo nixos-install --root /mnt --flake /mnt/path/to/flake#cachyos-to-nix
```

### Kernel Panic

**Problem**: System crashes during boot with panic messages.

**Solutions**:

```bash
# Check kernel logs
dmesg | tail -50

# Try older kernel
# In modules/system/boot.nix:
# boot.kernelPackages = pkgs.linuxPackages;  # Stable instead of latest

# Disable new kernel features
# Add to boot.nix:
boot.kernelParams = [ "no_console_suspend" "noapic" ];

# Rebuild and test
sudo nixos-rebuild switch --flake .#cachyos-to-nix
```

---

## Home-Manager Issues

### Home-Manager Conflicts

**Problem**: `home-manager` fails with "files already exist".

**Solutions**:

```bash
# Backup and retry
home-manager switch --flake /etc/nixos#radu --backup backup

# Or remove conflicting files
rm ~/.config/file.conf
home-manager switch --flake /etc/nixos#radu

# Or nuke and rebuild (if desperate)
rm -rf ~/.config ~/.local
home-manager switch --flake /etc/nixos#radu
```

### Powerlevel10k Not Working

**Problem**: Prompt looks broken or shows wrong characters.

**Solutions**:

```bash
# Run configuration wizard
p10k configure

# Install recommended fonts (in flake)
# Fonts already included, ensure they're set in terminal

# Check .p10k.zsh exists
ls -la ~/.config/zsh/.p10k.zsh

# If missing, run wizard again
p10k configure

# Check zsh version
zsh --version  # Should be 5.7+
```

### Git Configuration Not Applied

**Problem**: `git config` shows different values than flake.

**Solutions**:

```bash
# Verify home-manager applied it
home-manager switch --flake /etc/nixos#radu

# Check global config
git config --global --list

# Manually update if needed
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# In flake, update:
# home-manager/modules/shell/default.nix
# programs.git.userEmail = "new.email@example.com";
```

---

## Gaming Issues

### Steam Won't Launch

**Problem**: Steam crashes or won't start.

**Solutions**:

```bash
# Check steam service
ps aux | grep steam

# Clear steam cache
rm -rf ~/.cache/steam

# Verify 32-bit support
file /usr/bin/steam
ldd /usr/bin/steam

# Try launching with debug
steam -debug 2>&1 | head -50

# Check logs
cat ~/.local/share/Steam/logs/bootstrap_log.txt
```

### Proton Games Won't Run

**Problem**: Games fail to launch or crash immediately.

**Solutions**:

```bash
# Try different Proton version
# In Steam: Game > Properties > Compatibility > Change Proton version

# Check wine prefix
ls -la ~/.steam/root/compatibilitytools.d/

# Use protontricks
protontricks appid list-installed

# Run with verbose output
PROTON_LOG=1 steam run game.exe

# Clear shader cache
rm -rf ~/.cache/proton

# Rebuild with DXVK info:
cd ~/.steam/root/compatibilitytools.d/Proton-ge-*
DXVK_HUD=memory,fps ./proton-ge-custom run game.exe
```

### MangoHUD Not Showing

**Problem**: FPS counter and stats not visible in games.

**Solutions**:

```bash
# Enable globally
export MANGOHUD=1
steam

# Or per-game in Steam properties:
# Launch Options: MANGOHUD=1 %command%

# Check MangoHUD installed
which mangohud

# Verify config
cat ~/.config/MangoHUD/MangoHUD.conf

# Test outside steam
mangohud vulkaninfo
```

---

## Performance Issues

### System Is Slow

**Problem**: General slowness, high CPU usage.

**Solutions**:

```bash
# Check what's running
btop
top

# Check disk usage
du -sh ~/.cache/*
du -sh ~/.local/share/*

# Clean old packages
nix-collect-garbage -d
nix-store --optimise

# Check for resource leaks
journalctl -u systemd-oom -f
```

### High Memory Usage

**Problem**: RAM fills up quickly.

**Solutions**:

```bash
# Identify memory hogs
ps aux --sort=-%mem | head -10

# Restart memory-hungry services
sudo systemctl restart sddm

# Close unused applications
pgrep firefox  # Check for multiple instances

# Check swap
free -h
swapon --show
```

### Long Build Times

**Problem**: `nixos-rebuild` takes too long.

**Solutions**:

```bash
# Use substitutes from cache
# Should happen automatically, check:
nix eval --raw nixpkgs#hello

# Disable modules you don't need
# Comment out unused imports in:
# hosts/cachyos-to-nix/default.nix

# Use latest channel
nix flake update
```

---

## Network Issues

### No Internet Connection

**Problem**: Network doesn't work after boot.

**Solutions**:

```bash
# Check network status
sudo systemctl status NetworkManager

# Check interfaces
ip link
ip addr

# Try restarting networking
sudo systemctl restart NetworkManager

# Check gateway
ip route

# Ping DNS
ping 8.8.8.8
ping example.com

# Check DNS resolution
cat /etc/resolv.conf
nslookup example.com
```

### WiFi Not Connecting

**Problem**: WiFi network not visible or can't connect.

**Solutions**:

```bash
# Check WiFi is enabled
rfkill list
rfkill unblock wifi

# Check interfaces
nmcli device wifi list

# Connect manually
nmcli device wifi connect SSID --ask

# Check systemd-resolved
sudo systemctl status systemd-resolved

# Restart NetworkManager
sudo systemctl restart NetworkManager
```

---

## Audio Issues

### No Sound / Audio Muted

**Problem**: No audio output despite being unmuted.

**Solutions**:

```bash
# Check PipeWire
pactl info
pw-cli info

# Restart PipeWire
systemctl --user restart pipewire

# Check volume
pactl get-sink-mute @DEFAULT_SINK@
pactl set-sink-mute @DEFAULT_SINK@ 0

# List devices
pactl list sinks
pactl list sources

# Check pavucontrol GUI
pavucontrol
```

### Audio Cutting Out / Crackling

**Problem**: Audio distortion or stuttering.

**Solutions**:

```bash
# Check system load
btop

# Reduce CPU load (close apps)

# Check PipeWire config
cat ~/.config/pipewire/pipewire.conf

# Try different sample rate
# In pipewire config, adjust:
# default.clock.min-quantum = 32
# default.clock.quantum = 256

# Restart PipeWire
systemctl --user restart pipewire
```

---

## Display / GUI Issues

### Screen Flickering

**Problem**: Display flickers on and off.

**Solutions**:

```bash
# Check for driver conflicts
lsmod | grep -i video

# Try different refresh rate
# In KDE: System Settings > Display > Refresh Rate
# In GNOME: Settings > Displays

# Disable variable refresh
# In modules/hardware/nvidia.nix:
# hardware.nvidia.powerManagement.enable = true;

# Try Xorg instead of Wayland
```

### Wrong Screen Resolution

**Problem**: Resolution too high/low.

**Solutions**:

```bash
# List available resolutions
xrandr  # For Xorg
# or
kscreen-console  # For KDE

# Set resolution manually
xrandr --output HDMI-1 --mode 1920x1080

# Persistent in KDE:
# System Settings > Display and Monitor > Displays

# For GNOME:
# Settings > Displays > Resolution
```

### Dual Monitor Not Working

**Problem**: Second monitor not detected.

**Solutions**:

```bash
# List monitors
xrandr
kscreen-console

# Enable second monitor
xrandr --output HDMI-1 --auto --right-of DP-1

# In KDE, use System Settings
# In GNOME, use Settings > Displays

# For persistent config, create a script:
# ~/.local/bin/setup-monitors.sh
#!/bin/bash
xrandr --output HDMI-1 --auto --right-of DP-1
# Add to autostart
```

---

## Package / Dependency Issues

### Package Not Found

**Problem**: `nix build` or `home-manager` says package doesn't exist.

**Solutions**:

```bash
# Search for package
nix search nixpkgs your-package

# Check exact name
nix search nixpkgs 'your-package'

# Use flake for latest
nix flake update
sudo nixos-rebuild switch --flake .#cachyos-to-nix

# If package doesn't exist in nixpkgs:
# Add from nixpkgs:
# or from unstable channel
```

### Broken Dependencies

**Problem**: Build fails with "dependency not found".

**Solutions**:

```bash
# Check flake.lock
cat flake.lock

# Update inputs
nix flake update

# Check for conflicting versions
nix eval .#nixpkgs.system

# Full rebuild from scratch
sudo nixos-rebuild switch --flake .#cachyos-to-nix --keep-going
```

---

## Getting Help

### Check System Logs

```bash
# Recent system errors
journalctl -p 3 -xb

# Specific service
journalctl -u sddm -f

# Kernel messages
dmesg | tail -50

# Timeline
journalctl --since "2 hours ago"
```

### Enable Debug Output

```bash
# Verbose rebuild
sudo nixos-rebuild switch --flake .#cachyos-to-nix --show-trace -v 5

# Home-manager verbose
home-manager switch --flake /etc/nixos#radu -v
```

### Useful Resources

- **NixOS Docs**: https://nixos.org/manual/
- **NixOS Wiki**: https://nixos.wiki/
- **Nixpkgs Manual**: https://nixos.org/manual/nixpkgs/stable/
- **Home-manager**: https://nix-community.github.io/home-manager/
- **NixOS Discourse**: https://discourse.nixos.org/

---

If you're stuck, don't hesitate to:
1. Check logs (journalctl)
2. Search the NixOS wiki
3. Ask on NixOS Discourse
4. Check GitHub issues for similar problems
