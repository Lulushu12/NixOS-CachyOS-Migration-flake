# nixcfg-editor

A visual TUI for browsing and editing this repo's modular NixOS flake
configuration — add packages, enable/disable modules, and create new module
files without opening the `.nix` files by hand.

```
┌ nixcfg ── /etc/nixos/nixos-config ─────────────────────────────────────────┐
│ ⚙ System                          │  modules/gaming.nix                    │
│ ├─ hosts/nixos/default.nix        │  Gaming stack: Steam + Proton, Lutris, │
│ │  ├─ hardware-configuration 🔒   │  GameMode, MangoHud, RetroArch.        │
│ │  ├─ modules/common.nix          │                                        │
│ │  ├─ modules/gaming.nix          │  programs.steam.enable = true          │
│ │  │  └─ environment.systemPackages  programs.gamemode.enable = true       │
│ │  │     ├─ Launchers & managers  │  hardware.graphics.enable32Bit = true  │
│ │  │     │  ├─ lutris             │                                        │
│ │  │     │  └─ heroic             │  14 packages · 6 options               │
│ │  └─ modules/vm.nix (disabled)   │                                        │
│ └─ 🏠 Home                        │                                        │
│    └─ home/radu.nix …             │                                        │
└─ a add · space toggle · d remove · n new module · r reload · q quit ───────┘
```

## Running

On the NixOS machine (nix + git available — full functionality):

```bash
nix-shell -p "python3.withPackages (ps: [ ps.textual ])" \
  --run "python -m nixcfg.cli /etc/nixos/nixos-config"
```

or install it as a package: `pip install -e .` inside any Python ≥3.11
environment with `textual`, then:

```bash
nixcfg                  # autodetects: cwd upwards, then /etc/nixos
nixcfg path/to/config   # explicit (a flake.nix, its dir, or any dir below)
nixcfg --no-validate    # skip `nix flake check` on apply
nixcfg --no-commit      # don't git-commit applied changes
```

## Keyboard

Fully keyboard-driven (mouse works too):

| Key | Where | Action |
|---|---|---|
| `↑`/`↓` or `j`/`k` | tree | move cursor |
| `→`/`←` or `l`/`h` | tree | expand / collapse node (`←` on a leaf jumps to its parent) |
| `g` / `G` | tree | jump to top / bottom |
| `Shift+↑/↓` | tree | previous / next sibling |
| `Shift+←` | tree | jump to parent |
| `/` | tree | find — jumps as you type; `Enter` next match, `Esc` close |
| `a` | tree | add package to the highlighted module/list/section |
| `Space` | tree | enable/disable the highlighted package or module import |
| `c` | tree | edit the highlighted package's inline comment |
| `d` | tree | remove the highlighted package (with confirmation) |
| `n` | tree | new module under the highlighted module/branch |
| `u` | anywhere | undo the last applied change (`git revert`, with confirmation) |
| `e` | tree | open the highlighted file in `$EDITOR` at that line |
| `y` | tree | copy the highlighted name to the clipboard |
| `v` | anywhere | run `nix flake check` on demand |
| `r` | anywhere | reload config from disk |
| `?` | anywhere | help overlay with this key map |
| `Ctrl+P` | anywhere | command palette (every action, searchable) |
| `q` | anywhere | quit |
| `Tab` / `Shift+Tab` | dialogs | move between fields and buttons |
| `Enter` | dialogs | submit input / press focused button / pick search row |
| `Esc` | dialogs | cancel and close (disabled while an apply is running) |

`x` (extract to module) and `m` (move package) are reserved for the
Phase 2 multi-file operations.

## What it does

- **Tree browser**: starts at `flake.nix`, follows every `imports = [ … ]`
  recursively, and shows the whole config as a tree — system tree and
  home-manager tree, with disabled (commented-out) imports and read-only
  files marked.
- **Packages**: add (with `nix search` against the flake's pinned nixpkgs),
  remove, or comment-out/in any package, grouped by the config's
  `# ── Section ──` headers. Insertions match the surrounding style —
  indentation, aligned inline comments, section placement.
- **Modules**: enable/disable a whole module by toggling its import line;
  scaffold a new module file and wire its import into a parent of your choice.
- **Options**: shown per module (best-effort parse) for orientation;
  editing options is planned for a later phase.

## Safety model

Nothing is written blind:

1. every change is shown as a **diff** you confirm,
2. the flake is **validated** (`nix flake check --no-build`) after writing —
   on failure all files roll back automatically,
3. each applied change becomes **one git commit**, so `git revert` (or
   `git reset`) undoes it cleanly.

The parser is deliberately conservative: it recognizes the config's house
style (package lists, imports blocks, section headers, scalar options) and
edits only what it recognizes. Unrecognized syntax is displayed as-is and
never touched. `hardware-configuration.nix` and files whose header says
"do not edit" are refused for editing outright.

## Architecture

```
nixcfg/
├── cli.py          # entry point, config autodetection
├── core/           # UI-agnostic engine — no Textual imports
│   ├── model.py    # dataclasses for the parsed config
│   ├── parser.py   # section-aware Nix module parser
│   ├── graph.py    # flake.nix → import graph
│   ├── edits.py    # pure edit operations → EditPlan (before/after text)
│   ├── pipeline.py # write → validate → git commit, with rollback
│   └── search.py   # nix search wrapper (uses the flake.lock pin)
└── tui/            # Textual frontend (swappable — core has no UI deps)
```

The split is deliberate: a future web or GUI frontend reuses `core`
unchanged. (`textual serve "nixcfg"` already gives a browser version.)

## Development

```bash
python -m venv .venv && .venv/bin/pip install -e .[dev]
.venv/bin/python -m pytest tests/ -q
```

The test suite parses the repo's real `nixos-config/` and applies edits to
throwaway copies, asserting byte-exact formatting round-trips. `nix` is not
required for the tests (validation is mocked).
