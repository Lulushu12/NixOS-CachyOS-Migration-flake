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

    # ── Editors / IDEs ────────────────────────────────────────────────────────
    # Google Antigravity — agentic IDE (VS Code fork, unfree binary release).
    #
    # `.fhsWithPackages` wraps it in an FHS sandbox instead of installing the
    # bare derivation. Two reasons this matters here:
    #   1. Marketplace extensions ship pre-built ELF binaries that expect
    #      /usr/lib paths. Outside FHS they fail with "cannot open shared
    #      object file" and can only be fixed by patching them in nixpkgs.
    #   2. Antigravity's browser agent drives Playwright, which is hardcoded to
    #      look for a browser at /opt/google/chrome/chrome. The nixpkgs wrapper
    #      symlinks the first Chrome/Chromium it finds *inside the sandbox* to
    #      that path — so the browser has to be listed below, not just be
    #      installed on the host.
    #
    # Drop the google-chrome line (use plain `antigravity.fhs`) if you do not
    # want the browser agent; Brave/Vivaldi in apps.nix are not visible to it.
    (antigravity.fhsWithPackages (ps: with ps; [ google-chrome ]))

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
