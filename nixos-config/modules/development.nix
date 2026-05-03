# System-level development tools: compilers, debuggers, and build infrastructure.
#
# ─── Philosophy ──────────────────────────────────────────────────────────────
# This module installs things that belong at the system level:
#   • Compilers and linkers (gcc, clang, ld)
#   • Debuggers (gdb, lldb)
#   • Build system generators (cmake, make, autoconf)
#   • Low-level libraries and headers needed to compile things
#
# Language runtimes (Python, Node, Rust, Go) live in home/radu.nix.
# That way they are managed per-user and can be overridden per-project
# with `direnv` + `nix develop`.
#
# ─── Container support ───────────────────────────────────────────────────────
# Docker and Podman are commented out by default.
# To enable Docker:
#   1. Uncomment virtualisation.docker.enable below
#   2. Add "docker" to extraGroups in hosts/nixos/default.nix
#   3. Rebuild, then run `docker run hello-world` to verify
#
# To use Podman (rootless alternative):
#   1. Uncomment the virtualisation.podman section
#   2. No group membership needed — rootless by design

{ pkgs, config, ... }:

{
  environment.systemPackages = with pkgs; [

    # ── C / C++ ──────────────────────────────────────────────────────────────
    gcc             # GNU Compiler Collection (gcc, g++, gcov)
    clang           # LLVM C/C++ compiler — often friendlier error messages
    clang-tools     # clangd LSP, clang-format, clang-tidy
    cmake           # Cross-platform build system generator
    gnumake         # Classic `make` build tool
    ninja           # Fast parallel build system (used by cmake -G Ninja)
    pkg-config      # Query installed library paths for build systems
    gdb             # GNU debugger
    lldb            # LLVM debugger (pairs well with clang)
    valgrind        # Memory error detector and heap profiler
    ccache          # Compiler cache — dramatically speeds up rebuilds
    strace          # Trace system calls for debugging
    ltrace          # Trace library calls

    # ── General build tooling ─────────────────────────────────────────────────
    autoconf        # Build configuration script generator
    automake        # Makefile generator
    libtool         # Generic shared library support

    # ── Containers ────────────────────────────────────────────────────────────
    docker-compose  # Multi-container orchestration
    dive            # Explore Docker image layers interactively

    # ── Network / API tooling ─────────────────────────────────────────────────
    httpie          # Modern, human-friendly HTTP client (`http GET url`)
    websocat        # WebSocket testing (`websocat ws://...`)
    nmap            # Network scanner and port auditor

    # ── Code analysis / misc ──────────────────────────────────────────────────
    tokei           # Count lines of code by language
    hyperfine       # Benchmarking tool (`hyperfine 'cmd1' 'cmd2'`)
    meld            # Visual diff and merge tool (GUI)
    sqlite          # Embedded SQL database + CLI
    jless           # Pager for JSON files (like less but for JSON)

    # ── System / hardware tools ───────────────────────────────────────────────
    smartmontools   # SMART disk health monitoring (smartctl -a /dev/sda)
    hwinfo          # Detailed hardware information
    efibootmgr      # Manage UEFI boot entries from CLI
    config.boot.kernelPackages.cpupower  # CPU frequency scaling and governor control

    # ── Filesystem tools ──────────────────────────────────────────────────────
    btrfs-progs     # BTRFS filesystem CLI tools (balance, scrub, subvolume, etc.)
    btrfs-assistant # GUI for BTRFS snapshot and subvolume management
    snapper         # Automated BTRFS snapshot manager

  ];

  # ── Docker daemon ─────────────────────────────────────────────────────────
  # Uncomment to enable. Remember to add "docker" to extraGroups in default.nix.
  # virtualisation.docker = {
  #   enable      = true;
  #   autoPrune   = {
  #     enable = true;
  #     dates  = "weekly";
  #   };
  # };

  # ── Podman (rootless Docker alternative) ─────────────────────────────────
  # virtualisation.podman = {
  #   enable            = true;
  #   dockerCompat      = true;   # Provides a `docker` alias → podman
  #   defaultNetwork.settings.dns_enabled = true;
  # };
}
