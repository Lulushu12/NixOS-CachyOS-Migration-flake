"""Microphone capture and speaker playback.

Everything upstream (openWakeWord, faster-whisper, Piper) speaks 16 kHz mono
16-bit PCM, so that is the only format handled here. sounddevice talks to
PortAudio, which PipeWire exposes via its ALSA/Pulse compatibility layers — no
extra configuration is needed on this system.
"""

from __future__ import annotations

import asyncio
import logging
import queue

import numpy as np
import sounddevice as sd

_LOG = logging.getLogger("jarvis.audio")

RATE = 16000
WIDTH = 2  # bytes per sample (int16)
CHANNELS = 1
# 30 ms frames: the largest size webrtcvad accepts, and a comfortable chunk for
# the Wyoming services.
FRAME_MS = 30
FRAME_SAMPLES = RATE * FRAME_MS // 1000
FRAME_BYTES = FRAME_SAMPLES * WIDTH


class Microphone:
    """Continuous mic capture exposed as an async iterator of PCM frames.

    The PortAudio callback runs on its own thread, so frames land in a plain
    queue and are handed to asyncio via run_in_executor. The queue is bounded:
    if the consumer stalls we drop the oldest frames rather than growing without
    limit, because stale audio is worse than missing audio for wake detection.
    """

    def __init__(self, device: str | None = None, max_queued_frames: int = 100):
        self._device = device
        self._queue: queue.Queue[bytes] = queue.Queue(maxsize=max_queued_frames)
        self._stream: sd.RawInputStream | None = None
        self._level = 0.0

    @property
    def level(self) -> float:
        """Most recent RMS amplitude, 0.0–1.0. Drives the HUD waveform."""
        return self._level

    def _callback(self, indata, frames, time_info, status) -> None:
        if status:
            _LOG.debug("input stream status: %s", status)
        data = bytes(indata)
        samples = np.frombuffer(data, dtype=np.int16)
        if samples.size:
            rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))
            self._level = min(1.0, rms / 8000.0)
        try:
            self._queue.put_nowait(data)
        except queue.Full:
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(data)
            except queue.Empty:
                pass

    def start(self) -> None:
        self._stream = sd.RawInputStream(
            samplerate=RATE,
            blocksize=FRAME_SAMPLES,
            device=self._device,
            channels=CHANNELS,
            dtype="int16",
            callback=self._callback,
        )
        self._stream.start()
        _LOG.info("microphone open (device=%s)", self._device or "default")

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def drain(self) -> None:
        """Discard buffered audio — call before listening so the utterance
        does not begin with the tail of the wake word or the reply chime."""
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                return

    async def frames(self):
        # The blocking get is given a short timeout rather than waiting forever,
        # so consumers can notice a shutdown request between frames instead of
        # parking a worker thread until systemd loses patience and SIGKILLs us.
        loop = asyncio.get_running_loop()
        while True:
            try:
                frame = await loop.run_in_executor(None, self._queue.get, True, 0.25)
            except queue.Empty:
                continue
            yield frame


class Speaker:
    """Blocking playback, run off the event loop so audio never stalls asyncio."""

    def __init__(self, device: str | None = None):
        self._device = device

    async def play(self, pcm: bytes, rate: int = RATE) -> None:
        if not pcm:
            return
        samples = np.frombuffer(pcm, dtype=np.int16)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._play_blocking, samples, rate)

    def _play_blocking(self, samples: np.ndarray, rate: int) -> None:
        try:
            sd.play(samples, samplerate=rate, device=self._device, blocking=True)
        except Exception:  # a dead output device must not kill the daemon
            _LOG.exception("playback failed")

    async def chime(self, frequency: float = 880.0, duration: float = 0.12) -> None:
        """Short tone marking the transition into listening."""
        t = np.linspace(0, duration, int(RATE * duration), endpoint=False)
        envelope = np.minimum(1.0, np.minimum(t, duration - t) * 40)
        tone = np.sin(2 * np.pi * frequency * t) * envelope * 0.25
        await self.play((tone * 32767).astype(np.int16).tobytes())


class SilenceDetector:
    """Ends the user's turn after a run of non-speech frames.

    webrtcvad is aggressive-mode-2: strict enough to ignore fan noise and the
    desk, permissive enough not to clip quiet speech. Silence only counts once
    speech has started, so a slow start to the sentence is not treated as the end.
    """

    def __init__(self, silence_seconds: float = 1.2, aggressiveness: int = 2):
        import webrtcvad

        self._vad = webrtcvad.Vad(aggressiveness)
        self._needed = max(1, int(silence_seconds * 1000 / FRAME_MS))
        self._silent = 0
        self.speech_started = False

    def finished(self, frame: bytes) -> bool:
        if len(frame) != FRAME_BYTES:
            return False
        if self._vad.is_speech(frame, RATE):
            self.speech_started = True
            self._silent = 0
            return False
        if not self.speech_started:
            return False
        self._silent += 1
        return self._silent >= self._needed
