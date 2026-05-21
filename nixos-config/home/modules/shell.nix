{ pkgs, config, ... }:

{
  # ── Packages used by the shell (aliases, scripts, CLI tools) ───────────────
  home.packages = with pkgs; [
    rsync unzip htop tree p7zip unrar
    ripgrep bat eza fd fzf
    jq yq-go duf ncdu zoxide tldr
    nix-index  # command-not-found handler; referenced directly in initContent below
    pamixer    # scriptable PipeWire/PA volume control
  ];

  # ── CLI tools with Home Manager modules ────────────────────────────────────
  programs.btop.enable     = true;  # settings: share your btop.conf to fill in
  programs.cava.enable     = true;  # settings: share your cava config to fill in
  programs.fastfetch.enable = true; # settings: share your fastfetch config to fill in
  programs.micro.enable    = true;  # settings: share your micro config to fill in

  # ── Fish (secondary shell — primary is zsh) ────────────────────────────────
  # programs.fish = {
  #   enable = true;
  #   # TODO: share ~/.config/fish/config.fish to fill this in
  # };

  # ── ZSH ────────────────────────────────────────────────────────────────────

  programs.zsh = {
    enable            = true;
    enableCompletion  = true;
    autosuggestion.enable     = true;
    syntaxHighlighting.enable = true;

    history = {
      size       = 50000;
      save       = 50000;
      path       = "${config.xdg.dataHome}/zsh/history";
      ignoreDups = true;
      share      = true;
      extended   = true;
    };

    oh-my-zsh = {
      enable  = true;
      plugins = [
        "git"
        "sudo"
        "z"
        "colored-man-pages"
      ];
      theme = "";  # disabled — starship handles the prompt
    };

    shellAliases = {
      # NixOS management
      rebuild   = "sudo nixos-rebuild switch --flake /etc/nixos/nixos-config#nixos";
      testbuild = "sudo nixos-rebuild test --flake /etc/nixos/nixos-config#nixos";
      rollback  = "sudo nixos-rebuild switch --rollback";
      update    = "sudo nix flake update /etc/nixos/nixos-config && rebuild";
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

      # Git extras
      lg   = "lazygit";
      glog = "git log --oneline --graph --decorate --all";

      # Nix one-liners
      nsh  = "nix shell nixpkgs#";
      nrun = "nix run nixpkgs#";
    };

    initContent = ''
      # Ctrl+Backspace → delete previous word
      bindkey '^H' backward-kill-word

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

      # command-not-found handler — run `nix-index` once to build the database
      source ${pkgs.nix-index}/etc/profile.d/command-not-found.sh
    '';
  };

  # ── Starship prompt ────────────────────────────────────────────────────────

  programs.starship = {
    enable               = true;
    enableZshIntegration = true;
    settings = {
      add_newline     = true;
      command_timeout = 1000;
      directory.truncation_length = 3;
      directory.truncate_to_repo  = true;
      package.disabled            = true;
    };
  };
}
