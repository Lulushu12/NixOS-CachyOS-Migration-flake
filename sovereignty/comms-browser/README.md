# Comms & Browser De-Googling

Chat, search, browser, and (with heavy caveats) email.

## Decision: keep Zen (hardened), self-host SearXNG, keep Signal, skip Matrix

### Browser: Zen, hardened toward LibreWolf/Mullvad defaults

Zen was already in use and never actually vetted before this decision —
turns out it holds up: fully open source (MPL-2.0), maintained by "the
Zen Browser Team" on GitHub, no company, no VC, no telemetry, blocks
third-party trackers by default. Its focus is UX (workspaces, vertical
tabs) with solid privacy as a baseline, not maximum hardening as the
point — LibreWolf goes further by default (fingerprinting resistance, an
extension firewall, auto-clearing cookies) at the cost of more friction
(more re-logins, more sites needing a nudge). Given the pattern across
this whole plan — meaningfully more private over maximally locked down —
**keeping Zen and hardening it** was the right call over switching.

**How to harden it, closest-to-furthest from stock:**

1. **Start from [arkenfox/user.js](https://github.com/arkenfox/user.js)** —
   a community-maintained (no company, MPL-2.0), actively updated hardened
   `user.js` for Firefox-based browsers. This is most of what LibreWolf
   bakes in by default, as a drop-in file instead of a different browser.
   Drop it into Zen's profile folder (`about:support` → "Profile Folder")
   as `user.js`, alongside their `updater.sh` if you want it to track
   upstream changes. Use their "relaxed" overrides file if the "strict"
   defaults break too many sites you actually use.
2. **The highest-impact individual settings**, if you'd rather hand-pick
   instead of using the whole arkenfox file (`about:config`):
   - `privacy.resistFingerprinting` → `true` — standardizes your fingerprint (viewport, timezone, fonts) so you blend in with everyone else who has this on. This is the single biggest lever Mullvad Browser is built around.
   - `privacy.resistFingerprinting.letterboxing` → `true` — pairs with the above, pads the window to a fixed set of sizes.
   - `network.cookie.cookieBehavior` → `5` (total cookie protection / dFPI) — should already be Zen's default, worth confirming.
   - `dom.security.https_only_mode` → `true` — HTTPS-only, no silent downgrade.
   - `network.http.speculative-parallel-limit` → `0` and `network.dns.disablePrefetch` → `true` — stop prefetching links you hover but don't click.
   - `toolkit.telemetry.enabled` / `datareporting.healthreport.uploadEnabled` → `false` — belt-and-suspenders on top of Zen's own telemetry removal.
   - `app.shield.optoutstudies.enabled` → `false` — no Mozilla "Studies" (Zen forks Firefox, some of these prefs still exist even if unused).
   - `media.peerconnection.enabled` → `false` (or install a WebRTC-leak-guard extension) — stops WebRTC from leaking your real IP through Tailscale/VPN.
3. **Extensions: less is more.** Adding privacy extensions can paradoxically make you *more* fingerprintable (a unique combination of extensions is itself a signal) — this is why Mullvad Browser ships with almost none. If you add anything, uBlock Origin (in "advanced" mode, strict lists) is the one worth it; resist the urge to stack more on top.
4. **Not recommending an actual switch to LibreWolf or Mullvad Browser** — the above gets you most of the way there while keeping the UX you already like. Mullvad Browser specifically is designed to be used *with* Mullvad's VPN (its fingerprint-resistance model assumes everyone on it looks identical, which works best pooled through Mullvad's exit nodes) — without that, you lose part of its point anyway.

### Search: self-hosted SearXNG

Self-hosting (rather than a public instance or switching engines outright)
was picked because it directly solves the actual concern: SearXNG doesn't
replace DuckDuckGo, it *aggregates* engines (DuckDuckGo included) and lets
any of them be dropped or reweighted from one config file — so there's
"jump ship insurance" without migrating a search habit to a new provider
if DuckDuckGo is ever disliked later. It's also nearly stateless (no
personal data, no backups needed), making it one of the lowest-maintenance
items in this entire plan.

### Chat: Signal kept, Matrix/Conduit skipped, WhatsApp isolated (not replaced)

Contacts are on WhatsApp/Instagram/Messenger/iMessage and won't switch —
Signal doesn't interoperate with any of those (no reliable, ToS-compliant
bridge exists), and self-hosting Matrix has no payoff if nobody will
install a client. So: **Signal stays installed** for anyone open to it or
for future use, **Matrix/Conduit is skipped** (no audience = no win), and
**WhatsApp stays the official app** — no "privacy wrapper."

Specifically ruled out: **GBWhatsApp, WhatsApp Plus, FMWhatsApp** and
similar mod APKs. A 2025 IEEE Security & Privacy study analyzing these
found several more over-permissioned than the official app, and two
contained actual malware — built by anonymous third parties with no
guarantee the encryption is even intact, distributed outside app-store
scanning, and risking a temporary ban. **Do not install these.**

What actually helps, safely: **[Shelter](https://f-droid.org/packages/net.typeblog.shelter/)**
(F-Droid, fully open source, auditable) — uses Android's Work Profile
feature to run WhatsApp in an isolated sandbox with separate storage and
contacts, unable to see anything else on the phone. Doesn't touch
WhatsApp's server-side metadata collection (nothing client-side can), but
does stop it from seeing the rest of the device. This is a phone-level
tool, outside the scope of this NixOS flake.

### Email: out of scope for now

Self-hosting mail wasn't seriously considered — deliverability (avoiding
spam-folder purgatory) is a full-time job most providers spend a team on.
If de-googling email becomes a priority later, a privacy-respecting
*hosted* provider (Proton Mail, Tuta) is the realistic middle ground —
not covered by this round of decisions.

## Candidates considered

| Tool | Replaces | nixpkgs | Notes |
|---|---|---|---|
| **Zen (hardened) ✅** | Chrome/stock Firefox telemetry | Not in nixpkgs — community flakes exist (e.g. `0xc000022070/zen-browser-flake`, follows this repo's `nixpkgs`/`home-manager` inputs same as `claude-desktop`/`plasma-manager`) | **Decided.** Currently installed outside the flake; consider pulling in as a flake input for declarative management later. |
| **SearXNG ✅** | Google/Bing search | ✅ `pkgs.searxng` | **Decided.** Self-hosted, aggregates DuckDuckGo + others. |
| **Signal (kept) ✅** | SMS / unencrypted chat | ✅ `pkgs.signal-desktop` | **Decided**, but not a WhatsApp replacement — E2EE client kept for whoever's open to it. |
| Matrix (Conduit) + Element | Discord/Slack for personal/friend-group chat | ✅ `pkgs.matrix-conduit`, `pkgs.element-desktop` | Skipped — no audience willing to switch. |
| LibreWolf | Chrome/stock Firefox telemetry | ✅ `pkgs.librewolf` | Passed on in favor of hardening Zen instead — see above. |
| Self-hosted mail | Gmail/Outlook | external flake input | Ruled out — not recommended solo, see above. |

## Module stub

`nixos-config/modules/sovereignty/comms-browser.nix` — SearXNG stub,
`enable = false` by default. Zen and Signal are plain packages, not
services — add to `home/radu.nix`'s `home.packages` (or a flake input, for
Zen) when ready, no module needed.
