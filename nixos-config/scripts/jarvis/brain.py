"""The reasoning layer: a local Ollama model, Claude, or both.

Hybrid routing works in three stages:

  1. A cheap pre-check on the raw transcript. Long or explicitly hard requests
     go straight to Claude — running them locally first would just add latency
     before the escalation.
  2. The local model handles everything else. It has the full tool set plus an
     `escalate` tool it can call when it decides a request is beyond it.
  3. Any local failure — a crash, an empty answer, a malformed tool call —
     falls through to Claude rather than surfacing an error to the user.

Both brains see the same tools and the same system prompt, so which one answered
should be invisible apart from latency and quality.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from .config import Config
from .tools import ToolBox

_LOG = logging.getLogger("jarvis.brain")

MAX_TOOL_ROUNDS = 6

ESCALATE_TOOL = {
    "name": "escalate",
    "description": (
        "Hand this request to a more capable assistant. Call this when the "
        "request needs multi-step reasoning, detailed knowledge, writing, or "
        "careful judgement that you are not confident about. Prefer escalating "
        "over guessing."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"reason": {"type": "string"}},
        "required": [],
    },
}


def build_system_prompt(cfg: Config) -> str:
    parts = [
        f"You are {cfg.assistant_name}, a voice assistant running locally on "
        f"{cfg.user_name}'s NixOS desktop. You address the user as {cfg.user_name}.",
        "",
        "Your replies are spoken aloud by a speech synthesiser, so:",
        "- Answer in one or two short sentences unless asked for detail.",
        "- Write plain prose. No markdown, bullet points, code blocks, emoji, "
        "or symbols that cannot be read aloud.",
        "- Expand numbers, units, and abbreviations into words a speaker would "
        "say naturally.",
        "- Never describe the tool you are about to use; just use it and report "
        "the result.",
        "",
        "You control this machine through tools. When a request maps to a tool, "
        "call it rather than explaining how the user could do it themselves. "
        "When you genuinely cannot do something, say so in one sentence.",
    ]
    if cfg.personality.strip():
        parts += ["", cfg.personality.strip()]
    return "\n".join(parts)


class Brain:
    def __init__(self, cfg: Config, toolbox: ToolBox):
        self.cfg = cfg
        self.tools = toolbox
        self.system = build_system_prompt(cfg)
        self._anthropic = None
        self._ollama = None
        # Conversation history, kept short so a long session does not slow the
        # local model down or drift the context.
        self._history: list[dict[str, Any]] = []
        self._history_limit = 12

    # ── Clients ───────────────────────────────────────────────────────────────

    def _claude(self):
        if self._anthropic is None:
            import anthropic

            key = self.cfg.api_key()
            if not key:
                raise RuntimeError("no Anthropic API key available")
            self._anthropic = anthropic.Anthropic(api_key=key)
        return self._anthropic

    def _local(self):
        if self._ollama is None:
            import ollama

            self._ollama = ollama.Client(host=self.cfg.brain.ollama_host)
        return self._ollama

    # ── Routing ───────────────────────────────────────────────────────────────

    def _should_escalate_upfront(self, text: str) -> bool:
        lowered = text.lower()
        for hint in self.cfg.brain.escalate_hints:
            if hint.lower() in lowered:
                return True
        return len(text.split()) > self.cfg.brain.escalate_word_count

    async def think(self, transcript: str) -> str:
        mode = self.cfg.brain.mode

        if mode == "claude":
            return await self._run_claude(transcript)
        if mode == "local":
            return await self._run_local(transcript)

        # hybrid
        if self._should_escalate_upfront(transcript):
            _LOG.info("escalating up front (length/hint match)")
            return await self._run_claude(transcript)

        try:
            reply, escalated = await self._run_local(transcript, allow_escalation=True)
            if not escalated and reply.strip():
                return reply
            _LOG.info("local model escalated")
        except Exception:
            _LOG.exception("local brain failed, falling back to Claude")

        return await self._run_claude(transcript)

    def _remember(self, role: str, content: Any) -> None:
        self._history.append({"role": role, "content": content})
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit :]

    # ── Claude ────────────────────────────────────────────────────────────────

    async def _run_claude(self, transcript: str) -> str:
        client = self._claude()
        tools = self.tools.anthropic_schema()
        messages = list(self._history) + [{"role": "user", "content": transcript}]

        for _ in range(MAX_TOOL_ROUNDS):
            response = await asyncio.to_thread(
                client.beta.messages.create,
                model=self.cfg.brain.claude_model,
                max_tokens=self.cfg.brain.claude_max_tokens,
                # Opus 5's safety classifiers can decline a request outright.
                # "default" re-runs it on Anthropic's recommended fallback model
                # instead of handing the user a dead end.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                # Voice wants a fast first word; "low" keeps the pause short.
                # Thinking stays on (the default) — disabling it on Opus 5 can
                # make tool calls arrive as plain text that never execute.
                output_config={"effort": self.cfg.brain.claude_effort},
                system=self.system,
                tools=tools,
                messages=messages,
            )

            # A refusal returns HTTP 200 with empty or partial content, so this
            # has to be checked before touching response.content.
            if response.stop_reason == "refusal":
                _LOG.warning("Claude declined the request")
                return "I can't help with that one."

            if response.stop_reason != "tool_use":
                text = "".join(
                    block.text for block in response.content if block.type == "text"
                ).strip()
                self._remember("user", transcript)
                self._remember("assistant", text)
                return text or "I don't have an answer for that."

            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                output = await self.tools.call(block.name, dict(block.input))
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                    }
                )
            messages.append({"role": "user", "content": results})

        return "I got stuck working on that."

    # ── Local (Ollama) ────────────────────────────────────────────────────────

    async def _run_local(self, transcript: str, allow_escalation: bool = False):
        """Returns a string in local-only mode, or (reply, escalated) in hybrid."""
        client = self._local()
        tools = self.tools.ollama_schema()
        if allow_escalation:
            tools = tools + [
                {
                    "type": "function",
                    "function": {
                        "name": ESCALATE_TOOL["name"],
                        "description": ESCALATE_TOOL["description"],
                        "parameters": ESCALATE_TOOL["input_schema"],
                    },
                }
            ]

        messages = (
            [{"role": "system", "content": self.system}]
            + list(self._history)
            + [{"role": "user", "content": transcript}]
        )

        for _ in range(MAX_TOOL_ROUNDS):
            response = await asyncio.to_thread(
                client.chat,
                model=self.cfg.brain.local_model,
                messages=messages,
                tools=tools,
            )
            message = response.get("message", {}) or {}
            calls = message.get("tool_calls") or []

            if not calls:
                text = (message.get("content") or "").strip()
                self._remember("user", transcript)
                self._remember("assistant", text)
                return (text, False) if allow_escalation else text

            messages.append(message)
            for call in calls:
                fn = call.get("function", {}) or {}
                name = fn.get("name", "")
                raw_args = fn.get("arguments", {})
                # Ollama returns a dict for most models but a JSON string for some.
                if isinstance(raw_args, str):
                    try:
                        raw_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        raw_args = {}

                if name == "escalate":
                    return ("", True) if allow_escalation else ""

                output = await self.tools.call(name, raw_args)
                messages.append(
                    {"role": "tool", "name": name, "content": output}
                )

        stuck = "I got stuck working on that."
        return (stuck, True) if allow_escalation else stuck
