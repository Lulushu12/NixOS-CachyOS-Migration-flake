"""Orchestrator: wake word → listen → transcribe → think → speak → repeat.

One conversation turn is a strictly sequential pipeline, so the daemon holds a
single state at a time and the HUD mirrors it. The only concurrent work is the
wake-word reader task and the HUD level pump.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
import sys

from . import config as config_module
from .audio import Microphone, SilenceDetector, Speaker
from .brain import Brain
from .hud import Hud
from .tools import ToolBox
from .wyoming_io import WakeWordListener, synthesize, transcribe

_LOG = logging.getLogger("jarvis")

AFFIRMATIVE = {"yes", "yeah", "yep", "yes please", "do it", "go ahead", "confirm",
               "affirmative", "sure", "ok", "okay", "please do"}


class Assistant:
    def __init__(self, cfg):
        self.cfg = cfg
        self.mic = Microphone(cfg.input_device)
        self.speaker = Speaker(cfg.output_device)
        self.hud = Hud(cfg.hud_enabled, cfg.hud_port)
        self.wake = WakeWordListener(cfg.wake, cfg.wake_word)
        self.tools = ToolBox(cfg, confirm=self._confirm, notify=self._notify_tool)
        self.brain = Brain(cfg, self.tools)

        self._detected = asyncio.Event()
        self._reader: asyncio.Task | None = None
        self._stopping = asyncio.Event()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        await self.hud.start()
        self.mic.start()
        await self.wake.connect()
        self._reader = asyncio.create_task(self._wake_reader())
        await self.hud.state("idle")
        _LOG.info("%s ready — say the wake word", self.cfg.assistant_name)

    async def stop(self) -> None:
        self._stopping.set()
        if self._reader:
            self._reader.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader
        await self.wake.close()
        self.mic.stop()
        await self.hud.stop()

    async def _wake_reader(self) -> None:
        """Drain detection events from openWakeWord onto an asyncio.Event."""
        while not self._stopping.is_set():
            try:
                name = await self.wake.poll()
                if name:
                    _LOG.info("wake word detected (%s)", name)
                    self._detected.set()
            except asyncio.CancelledError:
                raise
            except Exception:
                _LOG.exception("wake connection lost, reconnecting in 2s")
                await asyncio.sleep(2)
                with contextlib.suppress(Exception):
                    await self.wake.close()
                    await self.wake.connect()

    # ── Turn pipeline ─────────────────────────────────────────────────────────

    async def run(self) -> None:
        while not self._stopping.is_set():
            await self._await_wake()
            if self._stopping.is_set():
                return
            try:
                await self._handle_turn()
            except Exception:
                _LOG.exception("turn failed")
                await self.hud.state("error")
                await self._say("Something went wrong on my end.")
            finally:
                await self.hud.state("idle", level=0.0, tool="")

    async def _await_wake(self) -> None:
        """Stream mic audio into openWakeWord until it fires."""
        self._detected.clear()
        self.mic.drain()
        async for frame in self.mic.frames():
            if self._stopping.is_set():
                return
            await self.wake.feed(frame)
            if self._detected.is_set():
                self._detected.clear()
                return

    async def _handle_turn(self) -> None:
        transcript = await self._listen()
        if not transcript:
            await self._say("I didn't catch that.")
            return

        _LOG.info("transcript: %s", transcript)
        await self.hud.state("thinking", transcript=transcript, reply="")

        reply = await self.brain.think(transcript)
        _LOG.info("reply: %s", reply)
        await self._say(reply)

    async def _listen(self) -> str:
        """Record until the user stops speaking, then transcribe."""
        await self.hud.state("listening", transcript="", reply="")
        self.hud.track_level(self.mic)
        await self.speaker.chime()
        self.mic.drain()

        detector = SilenceDetector(self.cfg.silence_seconds)
        frames: list[bytes] = []
        max_frames = int(self.cfg.max_utterance_seconds * 1000 / 30)

        async for frame in self.mic.frames():
            frames.append(frame)
            if detector.finished(frame) or len(frames) >= max_frames:
                break

        self.hud.stop_level()
        await self.hud.set(level=0.0)

        if not detector.speech_started:
            return ""
        return await transcribe(self.cfg.asr, frames)

    async def _say(self, text: str) -> None:
        if not text:
            return
        await self.hud.state("speaking", reply=text)
        pcm, rate = await synthesize(self.cfg.tts, text, self.cfg.tts_voice)
        await self.speaker.play(pcm, rate)
        # The wake listener was fed nothing while we spoke, but the mic queue
        # still captured our own voice — discard it so we do not wake ourselves.
        self.mic.drain()

    # ── Callbacks used by the tool layer ──────────────────────────────────────

    async def _notify_tool(self, description: str) -> None:
        await self.hud.set(tool=description)

    async def _confirm(self, prompt: str) -> bool:
        """Speak a yes/no question and listen for the answer.

        This is the guard on shell execution: a misheard command has to survive
        being read back to the user before anything runs.
        """
        await self._say(prompt)
        await self.hud.state("confirming", reply=prompt)
        answer = await self._listen()
        _LOG.info("confirmation answer: %r", answer)
        cleaned = answer.lower().strip().rstrip(".!")
        approved = cleaned in AFFIRMATIVE or cleaned.startswith(("yes", "yeah", "do it"))
        if not approved:
            await self._say("Cancelled.")
        return approved


async def _main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    cfg = config_module.load()
    assistant = Assistant(cfg)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, assistant._stopping.set)

    await assistant.start()
    try:
        await assistant.run()
    finally:
        await assistant.stop()
    return 0


def main() -> int:
    try:
        return asyncio.run(_main())
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
