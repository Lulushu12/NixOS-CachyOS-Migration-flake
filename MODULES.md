# Module Documentation

This document explains each module in detail, what it does, and how to customize it.

## System Modules (`modules/system/`)

### boot.nix

**Purpose**: Boot loader configuration, kernel settings, and early-stage system initialization.

**Key Settings**:
- GRUB bootloader with UEFI support
- Latest kernel packages
- Kernel parameters (quiet, splash)
- Optional Plymouth splash screen
- SSD TRIM support
- Systemd shutdown timeout

**Customization Examples**:

```nix
# Use stable kernel instead of latest:
boot.kernelPackages = pkgs.linuxPackages;

# Add kernel parameters for debugging:
boot.kernelParams = [ "quiet" "splash" "debug" ];

# Disable Plymouth splash screen:
boot.plymouth.enable = false;

# Use SYSTEMD-BOOT instead of GRUB:
# (Replace entire boot.loader section)
boot.loader.systemd-boot.enable = true;
boot.loader.efi.canTouchEfiVariables = true;
```

**When to Modify**:
- Changing bootloader
- Need different kernel versions
- Want custom kernel parameters
- Have boot-time issues

### localization.nix

**Purpose**: Timezone, locale, keyboard layout, and fonts.

**Key Settings**:
- Timezone: Europe/Bucharest
- Default locale: en_US.UTF-8
- Romanian language settings
- US/RO keyboard switching (Alt+Shift)
- System fonts

**Customization Examples**:

```nix
# Change timezone:
time.timeZone = "America/New_York";

# Change keyboard layout (US only):
services.xserver.xkb.layout = "us";

# Add more locales:
i18n.extraLocaleSettings = {
  LC_TIME = "en_US.UTF-8";
  LC_NUMERIC = "en_US.UTF-8";
};

# Add custom fonts:
fonts.packages = with pkgs; [
  jetbrains-mono
  source-code-pro
];
```

**When to Modify**:
- Change timezone
- Need different keyboard layout
- Use different language
- Want different fonts

### services.nix

**Purpose**: System services: audio, Bluetooth, printing, DNS, virtualization, power management.

**Key Services**:
- PipeWire (audio)
- Bluetooth with Blueman GUI
- CUPS printing with multiple drivers
- Avahi (mDNS/Bonjour)
- systemd-resolved (DNS)
- Docker
- UDisks2 (auto-mount USB drives)
- fstrim (SSD optimization)
- Smartd (disk monitoring)
- XDG portals (file dialogs)

**Customization Examples**:

```nix
# Enable libvirt for VMs:
virtualisation.libvirtd.enable = true;

# Change DNS provider:
services.resolved.servers = [ "8.8.8.8" "8.8.4.4" ];

# Disable Bluetooth:
hardware.bluetooth.enable = false;

# Enable more printing support:
services.printing.drivers = with pkgs; [
  # Add more drivers
];

# Auto-start Docker daemon:
virtualisation.docker.enableOnBoot = true;
```

**When to Modify**:
- Need a service not enabled by default
- Want to change audio/Bluetooth behavior
- Need printer support
- Using VMs or containers

---

## Hardware Modules (`modules/hardware/`)

### nvidia.nix

**Purpose**: NVIDIA RTX 2070 SUPER driver configuration.

**Key Settings**:
- Proprietary NVIDIA drivers (RTX 2070 uses Turing architecture)
- 32-bit support for games
- Vulkan and OpenGL support
- CUDA toolkit
- nvidia-settings GUI

**Customization Examples**:

```nix
# Use open-source drivers (newer cards):
hardware.nvidia.open = true;

# Enable CUDA for development:
environment.systemPackages = with pkgs; [
  cudatoolkit
  cudnn
];

# Custom NVIDIA settings:
hardware.nvidia.nvidiaSettings = true;

# Power management options:
powerManagement.enable = true;
powerManagement.resetModulesOnSleep = true;
```

**Troubleshooting**:

```bash
# Check driver version
nvidia-smi

# View detailed info
nvidia-settings

# Check for errors
dmesg | grep -i nvidia
```

**When to Modify**:
- Need CUDA for machine learning
- Experiencing driver issues
- Have different NVIDIA card
- Need custom power management

**Note**: RTX 2070 SUPER performs better with proprietary drivers. Only switch to open drivers if you have specific reasons.

---

## Desktop Modules (`modules/desktop/`)

### kde.nix

**Purpose**: KDE Plasma 6 desktop environment with all essential apps.

**Key Components**:
- Plasma Desktop
- Dolphin (file manager)
- Kate (text editor)
- Spectacle (screenshots)
- Okular (PDF viewer)
- KDE mail/calendar suite
- KDE system utilities

**Session Types Available**:
- Plasmawayland (Recommended for newer systems)
- Plasma (Xorg fallback)

**Customization Examples**:

```nix
# Add more KDE apps:
environment.systemPackages = with pkgs.kdePackages; [
  kdevelop  # IDE
  kaffeine  # Media player
  krita     # Drawing
];

# Change Phonon backend:
services.xserver.desktopManager.plasma6.phononBackend = "gstreamer";
```

**When to Use**:
- Want modern, feature-rich desktop
- Need traditional taskbar/widget approach
- Coming from KDE on CachyOS
- Want tight integration with system tools

### gnome.nix

**Purpose**: GNOME desktop environment alongside KDE.

**Key Components**:
- GNOME Shell
- Nautilus (file manager)
- GNOME Settings
- Evolution (mail/calendar)
- GNOME apps
- GNOME extensions support

**Session Types Available**:
- GNOME
- GNOME on Xorg (if Wayland has issues)

**Customization Examples**:

```nix
# Add more GNOME apps:
environment.systemPackages = with pkgs.gnome; [
  gnome-books
  gnome-photos
  gnome-music
];

# Enable specific extensions:
services.gnome.evolution-data-server.enable = true;
```

**Popular Extensions** (already configured):
- AppIndicator (system tray)
- Dash to Dock (custom dock)
- User Themes (custom themes)
- Blur My Shell (effects)

**When to Use**:
- Prefer modern, clean interface
- Like GNOME's app-centric approach
- Want to test GNOME on NixOS
- Need specific GNOME extensions

---

## Gaming Module (`modules/gaming/`)

### gaming.nix

**Purpose**: Complete gaming setup with Steam, Lutris, Proton, Wine, and performance tools.

**Included Tools**:
- **Steam**: Main gaming platform
- **Proton GE**: Cutting-edge compatibility for Windows games
- **Wine**: Direct Windows app/game support
- **Lutris**: Game manager for multiple platforms
- **MangoHUD**: FPS/performance overlay
- **GameMode**: CPU/GPU optimization
- **Emulators**: Dolphin, PCSX2, etc.
- **Utilities**: Antimicrox (controller mapper)

**Performance Features**:
- Auto gamemode for better FPS
- Kernel settings for gaming (vm.max_map_count)
- Vulkan/OpenGL support
- 32-bit library support for legacy games

**Customization Examples**:

```nix
# Disable gamemode if you don't want it:
programs.gamemode.enable = false;

# Increase map count for more demanding games:
boot.kernel.sysctl."vm.max_map_count" = 8589934592;

# Add more emulators:
environment.systemPackages = with pkgs; [
  mednafen    # Multi-system emulator
  mame        # Arcade games
];
```

**Using the Gaming Setup**:

```bash
# Launch Steam
steam

# Launch Lutris
lutris

# Launch a game with MangoHUD
mangohud %command%
# (Use in Steam game properties)

# Check performance
nvidia-smi -l 1  # Watch GPU usage
btop             # Watch CPU/RAM

# Game-specific Proton version:
# In Steam > Game Properties > Compatibility > Proton version
```

**Common Issues**:

```bash
# Wine/Proton 32-bit issues
# Make sure graphics.enable32Bit = true (should be set)

# Shader cache issues
# Delete: ~/.cache/wine
# Delete: ~/.cache/proton-ge

# Game won't launch
# Try different Proton versions
# Check: protontricks appid list-installed
```

**When to Modify**:
- Game has compatibility issues
- Want different emulators
- Need to enable features disabled by default
- Customizing performance settings

---

## Development Module (`modules/development/`)

### dev-tools.nix

**Purpose**: Comprehensive development environment with 317+ packages matching your CachyOS setup.

**Language Support**:
- Python (3.12)
- Rust (with cargo)
- Go
- Node.js (20.x with npm/pnpm)
- C/C++ (gcc, clang)
- Java
- PHP
- Ruby

**Key Tools**:
- **Build**: make, cmake, ninja, meson
- **Git**: Full git with LFS
- **Debuggers**: gdb, lldb, valgrind
- **Editors**: vim, nano, micro
- **IDEs**: VS Code, JetBrains community
- **Language Servers**: Rust-analyzer, Pylsp, Gopls
- **Docker**: Docker, docker-compose, podman
- **Containers**: Containerd
- **Web**: curl, wget, httpie, postman
- **Tools**: ripgrep, fd, fzf, bat, tmux

**Customization Examples**:

```nix
# Remove a language (e.g., Ruby):
# Delete from environment.systemPackages

# Add language-specific tools:
environment.systemPackages = with pkgs; [
  # Rust
  cargo-watch
  cargo-expand
  cargo-tree

  # Python
  poetry
  pdm
  
  # Node
  nodePackages.typescript
  yarn
];

# Enable direnv (for dev environment auto-loading):
programs.direnv.enable = true;  # Already set
```

**Using Development Tools**:

```bash
# Create a development environment with Nix
nix develop

# Or use direnv for auto-loading
echo 'use flake' > flake.nix
# direnv allow
# (auto-loads dev environment on cd)

# Language-specific workflows
cargo new project
npm init
python3 -m venv venv
go mod init
```

**When to Modify**:
- Need additional languages
- Want different IDEs
- Need specific library versions
- Adding language-specific tools

---

## Shell Module (`modules/shell/`)

### shell-config.nix

**Purpose**: System-level shell configuration, shell utilities, and tools.

**Shells Available**:
- **Zsh** (default, highly recommended)
- **Fish**
- **Bash** (fallback)

**Utilities Included**:
- **Modern replacements**: ripgrep, fd, fzf, bat, delta, exa, lsd
- **Terminal multiplexers**: tmux, screen
- **Text processing**: sed, awk, grep
- **System tools**: htop, btop, glances
- **Networking**: curl, wget, mtr, bind

**Customization Examples**:

```nix
# Change default shell to fish:
users.defaultUserShell = pkgs.fish;

# Add shell completions:
programs.bash.completion.enable = true;
programs.zsh.enableCompletion = true;

# Add custom packages:
environment.systemPackages = with pkgs; [
  your-favorite-tool
  another-utility
];
```

**When to Modify**:
- Want different shell as default
- Need additional command-line tools
- Want custom shell features

---

## Home-Manager Modules (`home-manager/modules/`)

### shell/default.nix

**Purpose**: User shell environment, Powerlevel10k, git config, direnv integration.

**Features**:
- **Powerlevel10k**: Advanced prompt with git integration
- **Zsh plugins**: Better completions and suggestions
- **Git**: Configured with your identity
- **Direnv**: Environment auto-loading for projects
- **fzf**: Fuzzy finder integration
- **bat**: Colored cat replacement
- **eza**: Modern ls replacement
- **tmux**: Terminal multiplexer setup

**Customization Examples**:

```nix
# Change git email:
programs.git.userEmail = "your.email@example.com";

# Customize git config:
programs.git.extraConfig = {
  core.editor = "vim";
  push.default = "current";
};

# Disable a tool:
programs.fzf.enable = false;

# Customize prompt (run p10k configure):
p10k configure
```

**Using the Shell**:

```bash
# Powerlevel10k configuration
p10k configure

# Direnv with Nix
echo 'use flake' > .envrc
direnv allow

# Git aliases (pre-configured)
gs   # git status
ga   # git add
gc   # git commit
gp   # git push
gl   # git log
```

**When to Modify**:
- Change git identity
- Add custom aliases
- Configure prompt
- Add shell plugins

### desktop/default.nix

**Purpose**: Desktop environment settings, GTK/Qt themes, MIME types, XDG configuration.

**Manages**:
- **GTK themes**: Breeze dark theme
- **Qt themes**: qt5ct configuration
- **Icons**: Breeze icons
- **Cursors**: Breeze cursors
- **MIME types**: File type associations
- **XDG dirs**: Standard directories

**Customization Examples**:

```nix
# Change GTK theme:
gtk.theme.name = "Arc-Dark";

# Change icon theme:
gtk.iconTheme.name = "Papirus";

# Add MIME type associations:
xdg.mimeApps.defaultApplications."text/plain" = "neovim.desktop";

# Change cursor size:
gtk.cursorTheme.size = 32;
```

**When to Modify**:
- Want different theme/icons
- Need to associate file types with apps
- Prefer different visual style

### desktop/kde.nix

**Purpose**: KDE Plasma specific home-manager configuration.

**Manages**:
- KDE-specific apps
- KDE settings files
- Qt environment variables
- Powerlevel10k for KDE terminal

**Note**: Configuration files reference templates in `kde-configs/` directory (which you can populate with your configs).

### desktop/gnome.nix

**Purpose**: GNOME specific home-manager configuration.

**Manages**:
- GNOME apps
- GNOME extensions
- Dconf settings
- Desktop preferences
- Workspaces
- Keybindings

**Dconf Settings** (all customizable):
- Dark theme preference
- Clock format (24h)
- Battery percentage display
- Favorite apps in dock
- Dock position and behavior
- File manager preferences
- Desktop background

**Customization Examples**:

```nix
# Change dock position to right:
"org/gnome/shell/extensions/dash-to-dock".dock-position = "RIGHT";

# Show battery:
"org/gnome/desktop/interface".show-battery-percentage = true;

# Add custom apps to favorites:
"org/gnome/shell".favorite-apps = [
  "firefox.desktop"
  "org.gnome.Nautilus.desktop"
  "code.desktop"
];
```

### development/default.nix

**Purpose**: User-level development tools, IDEs, language tools, version managers.

**Includes**:
- IDEs: VS Code, JetBrains, Sublime
- Language tools: Python, Rust, Go, Node.js
- API testing: Insomnia, Postman, HTTPie
- Database: DBeaver, SQLite browser
- Docker: lazydocker
- Git: lazygit, gh CLI
- Database: dbeaver

**Customization Examples**:

```nix
# Enable VS Code management by home-manager:
programs.vscode.enable = true;
programs.vscode.extensions = with pkgs.vscode-extensions; [
  # Add extensions
];

# Add Helix editor:
programs.helix.enable = true;
```

### media/default.nix

**Purpose**: Media and creative software: video, audio, image editing, 3D.

**Software**:
- **Video**: KDenlive, OBS, Shotcut, Handbrake
- **Audio**: Audacity, Ardour (DAW), Cmus
- **Image**: GIMP, Krita, Inkscape, Darktable
- **3D**: Blender, Meshlab
- **PDF**: Okular, Zathura
- **Ebook**: Calibre, Foliate

**Pre-configured**:
- VLC config
- MPV config with custom keybindings
- Audacity settings

**Customization Examples**:

```nix
# Add more apps:
home.packages = with pkgs; [
  aseprite    # Pixel art
  scribus     # Desktop publishing
];

# Customize MPV (great for anime):
home.file.".config/mpv/mpv.conf".text = ''
  profile=high-quality
  scale=ewa_lanczossharp
  dscale=mitchell
  cscale=mitchell
'';
```

### gaming/default.nix

**Purpose**: Gaming-specific home-manager configuration.

**Manages**:
- Steam configuration
- Lutris configuration
- MangoHUD settings
- Game-specific configs

**Pre-configured**:
- Steam directory structure
- Lutris game paths
- MangoHUD performance display

**Customization Examples**:

```nix
# Customize MangoHUD display:
home.file.".config/MangoHUD/MangoHUD.conf".text = ''
  fps
  cpu_stats
  gpu_stats
  ram
  position=top-left
  font_size=18
'';

# Add game-specific launchers
home.file.".local/bin/launch-game.sh" = {
  executable = true;
  text = ''#!/bin/bash
    export PROTON_USE_WINED3D=1
    gamemoderun wine "$@"
  '';
};
```

---

## Adding New Modules

### Example: Adding a Communication Module

Create `modules/desktop/communication.nix`:

```nix
{
  environment.systemPackages = with import <nixpkgs> {}; [
    # Messaging
    discord
    telegram-desktop
    slack
    matrix-clients.element-desktop

    # VoIP
    mumble
    teamspeak3

    # Email (already in KDE/GNOME)
  ];

  # Optional: Configure Mumble
  services.mumble.enable = false;  # Change to true if you want Mumble server
}
```

Add to `hosts/cachyos-to-nix/default.nix`:

```nix
imports = [
  # ... existing imports ...
  ../../modules/desktop/communication.nix
];
```

### Example: Adding a Customization Module

Create `modules/customization/cursor.nix`:

```nix
{
  environment.systemPackages = with import <nixpkgs> {}; [
    capitaine-cursors
    oxygen-cursors
  ];

  # Set cursor for X11
  services.xserver.displayManager.sessionCommands = ''
    xsetroot -cursor_name left_ptr
  '';
}
```

---

## Troubleshooting Modules

### Module Won't Build

```bash
# Check for syntax errors
nix eval /etc/nixos#nixosConfigurations.cachyos-to-nix

# Check specific module
nix eval -f /etc/nixos/modules/gaming/gaming.nix
```

### Package Not Found

```bash
# Search nixpkgs
nix search nixpkgs your-package

# Check which package set you're using
nix flake show
```

### Conflicting Modules

Remove from imports in `hosts/cachyos-to-nix/default.nix` to disable that module.

### Performance Issues

Check which module is slow:

```bash
time sudo nixos-rebuild switch --flake .#cachyos-to-nix
```

---

For more details on any module, read the inline comments in the Nix files themselves!
