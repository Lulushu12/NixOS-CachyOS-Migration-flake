"""Wyoming protocol clients for wake word, speech-to-text, and text-to-speech.

The three services run as systemd units managed by nixpkgs (see
modules/jarvis.nix). This daemon is purely a client: it streams microphone audio
to openWakeWord and faster-whisper, and pulls synthesised audio back from Piper.

Wyoming is a thin JSONL-over-TCP framing protocol; python3Packages.wyoming gives
us the event types, so nothing is hand-rolled here.
"""

from __future__ import annotations

import logging

from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncTcpClient
from wyoming.tts import Synthesize, SynthesizeVoice
from wyoming.wake import Detect, Detection

from .audio import CHANNELS, RATE, WIDTH
from .config import WyomingEndpoint

_LOG = logging.getLogger("jarvis.wyoming")


class WakeWordListener:
    """Holds a persistent connection to openWakeWord and reports detections.

    The connection stays open for the life of the daemon: reconnecting per
    utterance would add a round trip to every wake, and openWakeWord keeps its
    own rolling audio buffer that we do not want to reset.
    """

    def __init__(self, endpoint: WyomingEndpoint, model: str):
        self._endpoint = endpoint
        self._model = model
        self._client: AsyncTcpClient | None = None

    async def connect(self) -> None:
        self._client = AsyncTcpClient(self._endpoint.host, self._endpoint.port)
        await self._client.connect()
        # Naming the model explicitly keeps detection scoped to our wake word even
        # if the server has other models preloaded.
        await self._client.write_event(Detect(names=[self._model]).event())
        await self._client.write_event(
            AudioStart(rate=RATE, width=WIDTH, channels=CHANNELS).event()
        )
        _LOG.info("wake word listener connected (model=%s)", self._model)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None

    async def feed(self, frame: bytes) -> None:
        assert self._client is not None
        await self._client.write_event(
            AudioChunk(rate=RATE, width=WIDTH, channels=CHANNELS, audio=frame).event()
        )

    async def poll(self) -> str | None:
        """Return the detected model name, or None if nothing is pending.

        read_event() blocks until an event arrives, so this is only called from a
        task dedicated to draining the wake connection.
        """
        assert self._client is not None
        event = await self._client.read_event()
        if event is None:
            raise ConnectionError("wake word service closed the connection")
        if Detection.is_type(event.type):
            return Detection.from_event(event).name or self._model
        return None


async def transcribe(endpoint: WyomingEndpoint, frames: list[bytes]) -> str:
    """Send a complete utterance to faster-whisper and return the transcript."""
    async with AsyncTcpClient(endpoint.host, endpoint.port) as client:
        await client.write_event(Transcribe().event())
        await client.write_event(
            AudioStart(rate=RATE, width=WIDTH, channels=CHANNELS).event()
        )
        for frame in frames:
            await client.write_event(
                AudioChunk(
                    rate=RATE, width=WIDTH, channels=CHANNELS, audio=frame
                ).event()
            )
        await client.write_event(AudioStop().event())

        while True:
            event = await client.read_event()
            if event is None:
                return ""
            if Transcript.is_type(event.type):
                return (Transcript.from_event(event).text or "").strip()


async def synthesize(
    endpoint: WyomingEndpoint, text: str, voice: str | None = None
) -> tuple[bytes, int]:
    """Render text with Piper. Returns (pcm_bytes, sample_rate).

    Piper voices are not all 16 kHz — the rate comes back on the AudioStart
    event and is passed through to playback rather than assumed.
    """
    if not text.strip():
        return b"", RATE

    async with AsyncTcpClient(endpoint.host, endpoint.port) as client:
        request = Synthesize(text=text)
        if voice:
            request.voice = SynthesizeVoice(name=voice)
        await client.write_event(request.event())

        chunks: list[bytes] = []
        rate = RATE
        while True:
            event = await client.read_event()
            if event is None:
                break
            if AudioStart.is_type(event.type):
                rate = AudioStart.from_event(event).rate
            elif AudioChunk.is_type(event.type):
                chunk = AudioChunk.from_event(event)
                rate = chunk.rate or rate
                chunks.append(chunk.audio)
            elif AudioStop.is_type(event.type):
                break

        return b"".join(chunks), rate
