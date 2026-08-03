"""Tool definitions and execution.

Tools are declared once in Anthropic's schema shape and converted to Ollama's
OpenAI-style shape on the way out, so the local and remote brains see exactly the
same surface and a request behaves the same whichever one handles it.

Everything here runs as the user's own session — the daemon is a systemd *user*
unit, so it inherits the Wayland/DBus environment and can drive KDE directly.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any, Awaitable, Callable

from .config import Config

_LOG = logging.getLogger("jarvis.tools")

# Commands that are refused outright even with confirmation enabled. These are
# not a security boundary — anyone at the keyboard can run them — they exist so a
# misheard word can never become an unrecoverable action.
DEFAULT_DENY_PATTERNS = [
    r"\brm\s+(-[a-zA-Z]*\s+)*/(\s|$)",   # rm -rf /
    r"\bmkfs(\.|\s)",                     # formatting a filesystem
    r"\bdd\b.*\bof=/dev/",                # writing straight to a block device
    r">\s*/dev/[sn][dv][a-z]",            # same, via redirection
    r"\bshred\b",
    r":\(\)\s*\{.*\|.*&.*\}\s*;",        # fork bomb
]


async def _run(cmd: list[str], timeout: float = 15.0) -> tuple[int, str]:
    """Run a command without a shell and return (exit code, combined output)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except FileNotFoundError:
        return 127, f"{cmd[0]} is not installed"
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 124, "command timed out"
    return proc.returncode or 0, out.decode("utf-8", "replace").strip()


def _find_desktop_entry(name: str) -> str | None:
    """Locate a .desktop file by id or by fuzzy name match."""
    roots = [Path.home() / ".local/share/applications"]
    for base in os.environ.get(
        "XDG_DATA_DIRS", "/usr/share:/usr/local/share"
    ).split(":"):
        roots.append(Path(base) / "applications")

    needle = name.lower().replace(" ", "")
    fallback: str | None = None
    for root in roots:
        if not root.is_dir():
            continue
        for entry in sorted(root.glob("*.desktop")):
            stem = entry.stem.lower()
            if stem == needle or stem.endswith("." + needle):
                return str(entry)
            if fallback is None and needle in stem.replace(".", ""):
                fallback = str(entry)
    return fallback


class ToolBox:
    """Holds the enabled tool set and dispatches calls to implementations."""

    def __init__(
        self,
        cfg: Config,
        confirm: Callable[[str], Awaitable[bool]] | None = None,
        notify: Callable[[str], Awaitable[None]] | None = None,
    ):
        self.cfg = cfg
        # Called before a shell command runs. Returns True to proceed. The
        # orchestrator wires this to "speak the command, listen for yes/no".
        self._confirm = confirm
        # Called to surface a tool's activity on the HUD.
        self._notify = notify

        patterns = cfg.capabilities.shell.deny_patterns or DEFAULT_DENY_PATTERNS
        self._deny = [re.compile(p, re.IGNORECASE) for p in patterns]

    # ── Schemas ───────────────────────────────────────────────────────────────

    def anthropic_schema(self) -> list[dict[str, Any]]:
        caps = self.cfg.capabilities
        tools: list[dict[str, Any]] = []

        if caps.desktop:
            tools += [
                {
                    "name": "launch_app",
                    "description": (
                        "Open an application on the desktop. Use the common name "
                        "of the program, e.g. 'firefox', 'spotify', 'kate', "
                        "'steam'. Call this whenever the user asks to open, "
                        "start, or launch something."
                    ),
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Application name or binary",
                            }
                        },
                        "required": ["name"],
                    },
                },
                {
                    "name": "media_control",
                    "description": (
                        "Control whatever is currently playing audio or video "
                        "(Spotify, VLC, a browser tab). Call this for play, "
                        "pause, skip, previous, or to ask what is playing."
                    ),
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "play",
                                    "pause",
                                    "play-pause",
                                    "next",
                                    "previous",
                                    "stop",
                                    "status",
                                ],
                            }
                        },
                        "required": ["action"],
                    },
                },
                {
                    "name": "set_volume",
                    "description": (
                        "Change or query the system output volume. Call this for "
                        "'louder', 'quieter', 'mute', or 'set volume to 40'."
                    ),
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["set", "up", "down", "mute", "unmute", "get"],
                            },
                            "level": {
                                "type": "integer",
                                "description": "Percent 0-100, for 'set'; step size for up/down",
                            },
                        },
                        "required": ["action"],
                    },
                },
                {
                    "name": "switch_desktop",
                    "description": "Switch to a numbered KDE virtual desktop.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "number": {"type": "integer", "description": "1-based"}
                        },
                        "required": ["number"],
                    },
                },
            ]

        if caps.system:
            tools.append(
                {
                    "name": "system_status",
                    "description": (
                        "Read live machine health: CPU load, memory use, disk "
                        "free space, GPU temperature and VRAM. Call this when "
                        "asked how the machine is doing, or about temperatures, "
                        "memory, or free space."
                    ),
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "what": {
                                "type": "string",
                                "enum": ["all", "cpu", "memory", "disk", "gpu"],
                            }
                        },
                        "required": [],
                    },
                }
            )

        if caps.nixos:
            tools.append(
                {
                    "name": "nixos",
                    "description": (
                        "Query or manage the NixOS system. 'generations' and "
                        "'current' are read-only. 'rebuild', 'rollback', and "
                        "'garbage-collect' open a terminal window so the user can "
                        "enter their sudo password and watch the output."
                    ),
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "generations",
                                    "current",
                                    "rebuild",
                                    "rollback",
                                    "garbage-collect",
                                ],
                            }
                        },
                        "required": ["action"],
                    },
                }
            )

        if caps.shell.enabled:
            tools.append(
                {
                    "name": "run_shell",
                    "description": (
                        "Run a shell command on this machine and return its "
                        "output. Use this only when no other tool covers the "
                        "request. Prefer a single non-interactive command; it "
                        "cannot answer prompts. The user may be asked to confirm "
                        "out loud before it runs."
                    ),
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "reason": {
                                "type": "string",
                                "description": "One short phrase on why, spoken to the user when confirming",
                            },
                        },
                        "required": ["command"],
                    },
                }
            )

        return tools

    def ollama_schema(self) -> list[dict[str, Any]]:
        """Same tools in Ollama's OpenAI-compatible shape."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in self.anthropic_schema()
        ]

    # ── Dispatch ──────────────────────────────────────────────────────────────

    async def call(self, name: str, args: dict[str, Any]) -> str:
        _LOG.info("tool %s(%s)", name, json.dumps(args)[:200])
        if self._notify:
            await self._notify(f"{name} {json.dumps(args)[:80]}")
        handler = getattr(self, f"_tool_{name}", None)
        if handler is None:
            return f"No such tool: {name}"
        try:
            return await handler(args)
        except Exception as exc:  # a broken tool must not end the conversation
            _LOG.exception("tool %s failed", name)
            return f"Tool {name} failed: {exc}"

    # ── Implementations ───────────────────────────────────────────────────────

    async def _tool_launch_app(self, args: dict[str, Any]) -> str:
        name = str(args.get("name", "")).strip()
        if not name:
            return "No application name given."

        binary = shutil.which(name) or shutil.which(name.lower().replace(" ", "-"))
        if binary:
            # start_new_session detaches the app from the daemon's process group,
            # so restarting the service does not take the launched app with it.
            await asyncio.create_subprocess_exec(
                binary,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                start_new_session=True,
            )
            return f"Launched {name}."

        entry = _find_desktop_entry(name)
        if entry:
            code, out = await _run(["gio", "launch", entry])
            if code == 0:
                return f"Launched {name}."
            return f"Could not launch {name}: {out}"
        return f"I could not find an application called {name}."

    async def _tool_media_control(self, args: dict[str, Any]) -> str:
        action = str(args.get("action", "play-pause"))
        if action == "status":
            code, out = await _run(
                ["playerctl", "metadata", "--format", "{{artist}} — {{title}}"]
            )
            if code != 0 or not out:
                return "Nothing is playing."
            return f"Now playing: {out}"
        code, out = await _run(["playerctl", action])
        if code != 0:
            return f"Media control failed: {out or 'no player is running'}"
        return f"Media {action}."

    async def _tool_set_volume(self, args: dict[str, Any]) -> str:
        action = str(args.get("action", "get"))
        level = args.get("level")
        cmds = {
            "set": ["pamixer", "--set-volume", str(level if level is not None else 50)],
            "up": ["pamixer", "--increase", str(level or 10)],
            "down": ["pamixer", "--decrease", str(level or 10)],
            "mute": ["pamixer", "--mute"],
            "unmute": ["pamixer", "--unmute"],
            "get": ["pamixer", "--get-volume"],
        }
        code, out = await _run(cmds.get(action, cmds["get"]))
        if code != 0:
            return f"Volume control failed: {out}"
        if action == "get":
            return f"Volume is at {out} percent."
        _, now = await _run(["pamixer", "--get-volume"])
        return f"Volume is now {now} percent."

    async def _tool_switch_desktop(self, args: dict[str, Any]) -> str:
        number = int(args.get("number", 1))
        # gdbus rather than qdbus: it ships with glib, so there is no ambiguity
        # about which Qt version's tooling is on PATH under Plasma 6.
        code, out = await _run(
            [
                "gdbus",
                "call",
                "--session",
                "--dest", "org.kde.KWin",
                "--object-path", "/KWin",
                "--method", "org.kde.KWin.setCurrentDesktop",
                str(number),
            ]
        )
        if code != 0:
            return f"Could not switch desktop: {out}"
        return f"Switched to desktop {number}."

    async def _tool_system_status(self, args: dict[str, Any]) -> str:
        what = str(args.get("what", "all"))
        parts: list[str] = []

        if what in ("all", "cpu"):
            load = Path("/proc/loadavg").read_text().split()[:3]
            parts.append(f"Load average {load[0]}, {load[1]}, {load[2]}")

        if what in ("all", "memory"):
            meminfo = {}
            for line in Path("/proc/meminfo").read_text().splitlines():
                key, _, value = line.partition(":")
                meminfo[key] = int(value.strip().split()[0])
            total = meminfo["MemTotal"] / 1024 / 1024
            avail = meminfo["MemAvailable"] / 1024 / 1024
            parts.append(
                f"Memory {total - avail:.1f} of {total:.1f} gigabytes used"
            )

        if what in ("all", "disk"):
            usage = shutil.disk_usage("/")
            parts.append(
                f"Root filesystem {usage.free / 1e9:.0f} gigabytes free "
                f"of {usage.total / 1e9:.0f}"
            )

        if what in ("all", "gpu"):
            code, out = await _run(
                [
                    "nvidia-smi",
                    "--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ]
            )
            if code == 0 and out:
                temp, util, used, total = [v.strip() for v in out.split(",")]
                parts.append(
                    f"GPU at {temp} degrees, {util} percent utilised, "
                    f"{used} of {total} megabytes of VRAM in use"
                )

        return ". ".join(parts) + "." if parts else "No status available."

    async def _tool_nixos(self, args: dict[str, Any]) -> str:
        action = str(args.get("action", "current"))

        if action in ("generations", "current"):
            code, out = await _run(["nixos-rebuild", "list-generations"], timeout=30)
            if code != 0:
                return f"Could not read generations: {out}"
            lines = out.splitlines()
            if action == "current":
                current = next((l for l in lines if "current" in l.lower()), "")
                return f"Current generation: {current.strip() or 'unknown'}"
            return "Recent generations:\n" + "\n".join(lines[:6])

        # Mutating operations need a password and produce a lot of output, so
        # they go to a real terminal rather than running blind in the background.
        flake = "/etc/nixos/nixos-config#nixos"
        commands = {
            "rebuild": f"sudo nixos-rebuild switch --flake {flake}",
            "rollback": "sudo nixos-rebuild switch --rollback",
            "garbage-collect": "sudo nix-collect-garbage -d && nix-collect-garbage -d",
        }
        command = commands[action]
        terminal = shutil.which("kitty") or shutil.which("konsole")
        if not terminal:
            return "No terminal emulator available to run that in."
        await asyncio.create_subprocess_exec(
            terminal, "-e", "sh", "-c", f"{command}; echo; read -p 'Press enter to close'",
            start_new_session=True,
        )
        return f"Opened a terminal running {action}. You will need to enter your password."

    async def _tool_run_shell(self, args: dict[str, Any]) -> str:
        shell_cfg = self.cfg.capabilities.shell
        if not shell_cfg.enabled:
            return "Shell access is disabled."

        command = str(args.get("command", "")).strip()
        if not command:
            return "No command given."

        for pattern in self._deny:
            if pattern.search(command):
                _LOG.warning("refused command: %s", command)
                return (
                    "That command is on the refuse list and will not be run. "
                    "Run it yourself in a terminal if you meant it."
                )

        if shell_cfg.require_confirmation and self._confirm is not None:
            reason = str(args.get("reason", "")).strip()
            prompt = f"Run {command}?"
            if reason:
                prompt = f"To {reason}, run {command}?"
            if not await self._confirm(prompt):
                return "The user declined to run that command."

        _LOG.warning("executing shell command: %s", command)
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            out, _ = await asyncio.wait_for(
                proc.communicate(), timeout=shell_cfg.timeout_seconds
            )
        except asyncio.TimeoutError:
            proc.kill()
            return f"Command timed out after {shell_cfg.timeout_seconds} seconds."

        text = out.decode("utf-8", "replace").strip()
        # Voice replies are short; a huge dump helps nobody and costs tokens.
        if len(text) > 4000:
            text = text[:4000] + "\n… (output truncated)"
        return f"Exit code {proc.returncode}.\n{text or '(no output)'}"
