{ pkgs, ... }:

{
  home.packages = with pkgs; [

    # ── Python ────────────────────────────────────────────────────────────────
    (python3.withPackages (ps: with ps; [
      websockets   # audio visualizer widget transport
      dbus-python  # MPRIS media metadata queries
    ]))
    uv  # fast package/env manager

    # ── JavaScript / Node ─────────────────────────────────────────────────────
    nodejs_22
    pnpm

    # ── Rust ──────────────────────────────────────────────────────────────────
    rustup  # after first rebuild: rustup default stable

    # ── Go ────────────────────────────────────────────────────────────────────
    go
    gopls

    # ── Nix tooling ───────────────────────────────────────────────────────────
    nil          # language server
    statix       # linter
    deadnix      # find unused variables
    nh           # nicer nixos-rebuild wrapper
    nix-tree     # derivation dependency tree
    nix-diff     # diff two builds
    nvd          # package diffs between generations
    nixpkgs-fmt  # formatter

    # ── Git extras ────────────────────────────────────────────────────────────
    gh
    lazygit
    git-lfs

  ];

  # ── Git ───────────────────────────────────────────────────────────────────

  programs.git = {
    enable = true;
    # Set identity locally — never commit name/email to the repo:
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
  };

  programs.delta = {
    enable               = true;
    enableGitIntegration = true;
    options = {
      navigate     = true;
      line-numbers = true;
      dark         = true;
      syntax-theme = "TwoDark";
    };
  };

  # ── Direnv  (per-project Nix environments) ────────────────────────────────

  programs.direnv = {
    enable               = true;
    enableZshIntegration = true;
    nix-direnv.enable    = true;
  };
}
