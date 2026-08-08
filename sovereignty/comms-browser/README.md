# Comms & Browser De-Googling

Chat, search, browser, and (with heavy caveats) email.

## Candidates

| Tool | Replaces | nixpkgs | NixOS option | Effort | Notes |
|---|---|---|---|---|---|
| LibreWolf | Chrome/stock Firefox telemetry | ✅ `pkgs.librewolf` | n/a — `home.packages` | Trivial | Hardened Firefox fork, telemetry stripped, sane defaults. Drop-in. |
| SearXNG | Google/Bing search | ✅ `pkgs.searxng` | `services.searx` | Low-Medium | Self-hosted metasearch aggregator — queries other engines on your behalf so no single one profiles you. Can also just use a public SearXNG instance with zero hosting if you don't want to run it yourself. |
| Signal (client only) | SMS / unencrypted chat | ✅ `pkgs.signal-desktop` | n/a — `home.packages` | Trivial | Best-in-class E2EE, but the *server* is Signal's, centralized. Not "sovereign" infra, just genuinely private comms — worth having regardless. |
| Matrix (Conduit) | Discord/Slack for personal/friend-group chat | ✅ `pkgs.matrix-conduit` | `services.matrix-conduit` | Medium | Lightweight Matrix homeserver (single binary, unlike Synapse). Real sovereignty win but only pays off if the people you talk to will actually switch. |
| Element | Discord/Slack client | ✅ `pkgs.element-desktop` | n/a — `home.packages` | Trivial | Matrix client, pairs with Conduit above. |
| Self-hosted mail (e.g. `simple-nixos-mailserver`) | Gmail/Outlook | external flake input | n/a | Very high | **Not recommended solo.** Deliverability (avoiding spam-folder purgatory) requires ongoing reputation management most providers spend a team on. If email sovereignty matters, a privacy-respecting *hosted* provider (Proton Mail, Tuta) is the pragmatic middle ground — you keep E2EE and no ad-scanning, without running your own MTA. |

## Recommendation

**LibreWolf** and **Signal** are zero-cost swaps — just packages, add them
whenever. **SearXNG** is worth running if you're already comfortable
maintaining the DNS/networking modules, otherwise use a public instance.
Matrix only makes sense if you can get others to join you there — don't
self-host a chat server for an audience of one. Leave self-hosted email off
the table entirely; use Proton/Tuta if that itch needs scratching.

## Module stub

`nixos-config/modules/sovereignty/comms-browser.nix` — SearXNG and Conduit
stubs, `enable = false` by default. LibreWolf/Signal/Element are just
packages — add them directly to `home/radu.nix` when wanted.
