# Home Manager configuration for user "radu".
#
# Manages everything at the user level:
#   • Packages installed just for you
#   • Shell (zsh) + prompt (starship) configuration
#   • Terminal emulator (kitty)
#   • Theming (GTK dark mode, Qt)
#   • Git defaults
#   • Dot-files for Niri, Waybar, Mako, Fuzzel
#
# Apply changes:   rebuild   (alias defined below)

{ pkgs, config, ... }:

{
  home.stateVersion  = "24.11";
  home.username      = "radu";
  home.homeDirectory = "/home/radu";

  # ── Session environment variables ──────────────────────────────────────────
  home.sessionVariables = {
    EDITOR  = "kate";
    VISUAL  = "kate";
    BROWSER = "brave";
    # Native Wayland rendering for Electron apps (Obsidian, etc.)
    NIXOS_OZONE_EL     = "1";
    # Native Wayland for Firefox-based browsers (Brave, Mullvad, etc.)
    MOZ_ENABLE_WAYLAND = "1";
    # Qt Wayland backend with X11 fallback
    QT_QPA_PLATFORM    = "wayland;xcb";
  };

  # ════════════════════════════════════════════════════════════════════════════
  # PACKAGES
  # ════════════════════════════════════════════════════════════════════════════

  home.packages = with pkgs; [

    # ── Browsers ──────────────────────────────────────────────────────────────
    brave            # Chromium-based, built-in ad/tracker blocking
    vivaldi          # Feature-rich Chromium browser (unfree)
    mullvad-browser  # Privacy-hardened Firefox build

    # ── Multimedia: video / audio ─────────────────────────────────────────────
    vlc              # Universal media player
    spotify          # Music streaming (unfree)
    obs-studio       # Screen recording and streaming

    # ── Multimedia: image / vector ────────────────────────────────────────────
    gimp                      # Raster image editor
    inkscape-with-extensions  # Vector graphics editor (full)

    # ── Multimedia: video editing ─────────────────────────────────────────────
    kdePackages.kdenlive  # Non-linear video editor (KDE-native)
    # davinci-resolve  # DISABLED in VM: requires a real GPU.
    #                  # Uncomment on bare metal with a working GPU driver.

    # ── 3D / creative ─────────────────────────────────────────────────────────
    blender          # 3D modelling and animation (CPU rendering in VM — slow but works)

    # ── Communication ─────────────────────────────────────────────────────────
    vesktop          # Open-source Discord client

    # ── Productivity ──────────────────────────────────────────────────────────
    libreoffice-fresh  # Full office suite
    obsidian           # Markdown knowledge base (unfree)

    # ── Dev: Python ───────────────────────────────────────────────────────────
    python3  # Python 3 interpreter
    uv       # Fast package/env manager (replaces pip + pyenv + venv)

    # ── Dev: JavaScript / Node ────────────────────────────────────────────────
    nodejs_22   # Node.js LTS (includes npm and npx)
    pnpm        # Fast, disk-efficient package manager

    # ── Dev: Rust ─────────────────────────────────────────────────────────────
    # After first rebuild: rustup default stable
    rustup

    # ── Dev: Go ───────────────────────────────────────────────────────────────
    go       # Go compiler
    gopls    # Go language server (includes modernize and other tools in 0.21+)

    # ── Dev: Nix ──────────────────────────────────────────────────────────────
    nil        # Nix language server (autocomplete for .nix files)
    statix     # Nix linter
    deadnix    # Find unused variables in .nix files
    nh         # Nicer nixos-rebuild wrapper (`nh os switch`)
    nix-tree   # Visualise derivation dependency tree
    nix-diff   # Diff two Nix builds
    nvd        # Show package diffs between generations
    nixpkgs-fmt  # Format .nix files

    # ── Dev: misc ─────────────────────────────────────────────────────────────
    gh        # GitHub CLI
    lazygit   # Terminal UI for git
    git-lfs   # Git Large File Storage extension

    # ── Communication ─────────────────────────────────────────────────────────
    discord   # Official Discord client

    # ── Music ─────────────────────────────────────────────────────────────────
    spotify-player  # TUI Spotify client

    # ── Remote desktop ────────────────────────────────────────────────────────
    anydesk   # Remote desktop (unfree)

    # ── Creative / CAD ────────────────────────────────────────────────────────
    freecad       # Parametric 3D CAD modeler
    onlyoffice-desktopeditors # MS Office-compatible suite (unfree)

    # ── Cloud / sync ──────────────────────────────────────────────────────────
    rclone    # Sync to/from Google Drive, S3, etc.

    # ── Wayland tools ─────────────────────────────────────────────────────────
    wofi      # Wayland app launcher (alternative to KRunner)
    pamixer   # CLI PipeWire/PulseAudio volume control (scriptable)

    # ── Terminal utilities ─────────────────────────────────────────────────────
    fastfetch # System info display
    cava      # Terminal audio visualizer
    micro     # Minimal terminal text editor
    rsync     # File sync and backup
    unzip     # Extract .zip archives
    htop      # Process viewer
    btop      # Visual resource monitor
    tree      # Directory tree printer
    ripgrep   # Fast text search (rg)
    bat       # Better cat (syntax highlighting)
    eza       # Better ls (icons, git status)
    fd        # Better find
    fzf       # Fuzzy finder (Ctrl+R, Ctrl+T)
    jq        # JSON processor
    yq-go     # Like jq for YAML/TOML/XML
    duf       # Visual disk usage (df replacement)
    ncdu      # Interactive disk usage browser
    zoxide    # Smart cd that learns your dirs
    tldr      # Simplified man pages
    nix-index # Package-to-file index (command-not-found handler)
    p7zip     # 7-Zip CLI
    unrar     # Extract .rar archives

  ];

  # ════════════════════════════════════════════════════════════════════════════
  # SHELL: ZSH
  # ════════════════════════════════════════════════════════════════════════════

  programs.zsh = {
    enable            = true;
    enableCompletion  = true;
    autosuggestion.enable     = true;  # Grey suggestion as you type
    syntaxHighlighting.enable = true;  # Green = valid cmd, red = not found

    history = {
      size       = 50000;
      save       = 50000;
      path       = "${config.xdg.dataHome}/zsh/history";
      ignoreDups = true;
      share      = true;   # Shared across all terminal windows
      extended   = true;   # Save timestamps
    };

    oh-my-zsh = {
      enable  = true;
      plugins = [
        "git"                # Aliases: gst, gcmsg, gp, gl, gd, gco, gcb…
        "sudo"               # Esc Esc → prepend sudo to last command
        "z"                  # `z proj` → jump to ~/code/my-project
        "colored-man-pages"  # Syntax-highlighted man pages
      ];
      theme = "";  # Disabled — starship handles the prompt
    };

    shellAliases = {
      # NixOS management
      # Assumes the repo is cloned/symlinked to /etc/nixos.
      # If you keep it elsewhere (e.g. ~/nixos-config), update this path.
      rebuild   = "sudo nixos-rebuild switch --flake /etc/nixos#nixos";
      testbuild = "sudo nixos-rebuild test --flake /etc/nixos#nixos";
      rollback  = "sudo nixos-rebuild switch --rollback";
      update    = "sudo nix flake update /etc/nixos && rebuild";
      clean     = "sudo nix-collect-garbage -d && nix-collect-garbage -d";

      # Better defaults
      ls   = "eza --icons";
      ll   = "eza -la --icons --git";
      la   = "eza -a --icons";
      lt   = "eza --tree --icons";
      cat  = "bat --paging=never";
      grep = "rg";
      find = "fd";
      cd   = "z";

      # Navigation
      ".."   = "z ..";
      "..."  = "z ../..";
      "...." = "z ../../..";

      # Git extras (beyond oh-my-zsh git plugin)
      lg   = "lazygit";
      glog = "git log --oneline --graph --decorate --all";

      # Nix one-liners
      nsh  = "nix shell nixpkgs#";   # nsh ripgrep → temp shell with ripgrep
      nrun = "nix run nixpkgs#";     # nrun cowsay -- hello
    };

    initContent = ''
      # zoxide — must be initialised after oh-my-zsh
      eval "$(zoxide init zsh)"

      # Show NixOS generation info
      nixgen() {
        echo "=== Current generation ==="
        nixos-rebuild list-generations | grep current
        echo ""
        echo "=== Recent generations (newest first) ==="
        nixos-rebuild list-generations | tail -n +2 | head -10
      }

      # Find what installed a given binary
      nixwhy() { nix-store --query --referrers "$(which "$1")"; }

      # command-not-found: suggests the nixpkgs package that contains a missing command.
      # Run `nix-index` once to build the database (~10 min).
      source ${pkgs.nix-index}/etc/profile.d/command-not-found.sh
    '';
  };

  # ════════════════════════════════════════════════════════════════════════════
  # PROMPT: STARSHIP
  # ════════════════════════════════════════════════════════════════════════════

  programs.starship = {
    enable               = true;
    enableZshIntegration = true;
    settings = {
      add_newline     = true;
      command_timeout = 1000;
      directory.truncation_length   = 3;
      directory.truncate_to_repo    = true;
      package.disabled              = true;
    };
  };

  # ════════════════════════════════════════════════════════════════════════════
  # TERMINAL: KITTY  (Tokyo Night colour scheme)
  # ════════════════════════════════════════════════════════════════════════════

  programs.kitty = {
    enable = true;
    font   = { name = "JetBrainsMono Nerd Font"; size = 13; };
    settings = {
      # Colours
      background           = "#1a1b26";
      foreground           = "#c0caf5";
      selection_background = "#283457";
      selection_foreground = "#c0caf5";
      cursor               = "#c0caf5";
      cursor_text_color    = "#1a1b26";
      url_color            = "#73daca";

      color0  = "#15161e";  color8  = "#414868";
      color1  = "#f7768e";  color9  = "#f7768e";
      color2  = "#9ece6a";  color10 = "#9ece6a";
      color3  = "#e0af68";  color11 = "#e0af68";
      color4  = "#7aa2f7";  color12 = "#7aa2f7";
      color5  = "#bb9af7";  color13 = "#bb9af7";
      color6  = "#7dcfff";  color14 = "#7dcfff";
      color7  = "#a9b1d6";  color15 = "#c0caf5";

      # Behaviour
      background_opacity    = "0.95";
      window_padding_width  = 8;
      scrollback_lines      = 10000;
      enable_audio_bell     = false;
      copy_on_select        = "clipboard";
      strip_trailing_spaces = "smart";

      # Tab bar
      hide_window_decorations = "yes";
      tab_bar_style           = "powerline";
      tab_bar_min_tabs        = 2;
    };
  };

  # ════════════════════════════════════════════════════════════════════════════
  # MEDIA PLAYER: MPV
  # ════════════════════════════════════════════════════════════════════════════

  programs.mpv = {
    enable = true;
    config = {
      profile               = "gpu-hq";
      vo                    = "gpu";
      hwdec                 = "auto-safe";
      sub-auto              = "fuzzy";
      volume                = 75;
      save-position-on-quit = true;
    };
  };

  # ════════════════════════════════════════════════════════════════════════════
  # GIT
  # ════════════════════════════════════════════════════════════════════════════

  programs.git = {
    enable = true;
    # No name/email here — set locally with:
    #   git config --global user.name  "Your Name"
    #   git config --global user.email "you@example.com"
    signing.format = null;
    settings = {
      init.defaultBranch   = "main";
      pull.rebase          = true;
      push.autoSetupRemote = true;
      core.editor          = "vim";
      merge.conflictstyle  = "diff3";
      alias.lg   = "log --oneline --graph --decorate --all";
      alias.undo = "reset HEAD~1 --mixed";
      alias.wip  = "commit -am 'WIP'";
    };
    delta = {
      enable  = true;
      options = {
        navigate     = true;
        line-numbers = true;
        dark         = true;
        syntax-theme = "TwoDark";
      };
    };
  };

  # ════════════════════════════════════════════════════════════════════════════
  # DIRENV  (per-project Nix environments)
  # ════════════════════════════════════════════════════════════════════════════

  programs.direnv = {
    enable               = true;
    enableZshIntegration = true;
    nix-direnv.enable    = true;
  };

  # ════════════════════════════════════════════════════════════════════════════
  # THEMING: GTK
  # ════════════════════════════════════════════════════════════════════════════
  # GTK theming is intentionally left to KDE Plasma. KDE writes to
  # ~/.gtkrc-2.0 and ~/.config/gtk-{3,4}.0/ on every login, which conflicts
  # with Home Manager symlinks and causes HM activation to fail repeatedly.
  # KDE applies Breeze-Dark to GTK apps automatically via its GTK settings
  # module, so no HM management is needed.

  # ════════════════════════════════════════════════════════════════════════════
  # THEMING: QT (mirrors GTK dark mode)
  # ════════════════════════════════════════════════════════════════════════════

  qt = {
    enable             = true;
    platformTheme.name = "kde";
    style = { name = "breeze"; package = pkgs.kdePackages.breeze; };
  };

  # ════════════════════════════════════════════════════════════════════════════
  programs.home-manager.enable = true;
}
