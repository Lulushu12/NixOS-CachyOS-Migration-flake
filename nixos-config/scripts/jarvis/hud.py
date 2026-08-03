"""WebSocket bridge to the Plasma HUD widget.

The daemon owns the state; the widget is a pure view. State is pushed on every
change, and while the assistant is listening or speaking a level value is pushed
continuously so the widget can animate the waveform.

This mirrors the transport the existing audio-visualizer widget already uses, so
the same Python environment and the same Plasma applet pattern apply.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any

_LOG = logging.getLogger("jarvis.hud")

try:  # websockets >= 14 moved the server; the old alias still works but warns
    from websockets.asyncio.server import serve as _serve
except ImportError:  # pragma: no cover - older websockets
    from websockets import serve as _serve  # type: ignore[attr-defined]


class Hud:
    """Broadcasts assistant state to any connected widget.

    Nothing here is load-bearing: if the HUD is disabled or no widget is
    connected, every method is a cheap no-op and the assistant behaves the same.
    """

    def __init__(self, enabled: bool = True, port: int = 8770):
        self.enabled = enabled
        self.port = port
        self._clients: set[Any] = set()
        self._server = None
        self._pump: asyncio.Task | None = None
        self._state: dict[str, Any] = {
            "state": "idle",
            "level": 0.0,
            "transcript": "",
            "reply": "",
            "tool": "",
        }

    async def start(self) -> None:
        if not self.enabled:
            return
        self._server = await _serve(self._handle, "127.0.0.1", self.port)
        _LOG.info("HUD listening on ws://127.0.0.1:%d", self.port)

    async def stop(self) -> None:
        if self._pump:
            self._pump.cancel()
        if self._server is not None:
            self._server.close()
            with contextlib.suppress(Exception):
                await self._server.wait_closed()

    async def _handle(self, websocket) -> None:
        self._clients.add(websocket)
        try:
            # Send current state immediately so a widget that connects mid-session
            # is not blank until the next transition.
            await websocket.send(json.dumps(self._state))
            async for _ in websocket:
                pass  # the widget never sends anything; just hold the connection
        except Exception:
            pass
        finally:
            self._clients.discard(websocket)

    async def _broadcast(self) -> None:
        if not self._clients:
            return
        payload = json.dumps(self._state)
        dead = []
        for client in list(self._clients):
            try:
                await client.send(payload)
            except Exception:
                dead.append(client)
        for client in dead:
            self._clients.discard(client)

    async def set(self, **fields: Any) -> None:
        if not self.enabled:
            return
        self._state.update(fields)
        await self._broadcast()

    async def state(self, name: str, **fields: Any) -> None:
        await self.set(state=name, **fields)

    def track_level(self, source) -> None:
        """Stream `source.level` to the widget until stop_level() is called."""
        if not self.enabled:
            return
        self.stop_level()
        self._pump = asyncio.create_task(self._level_loop(source))

    def stop_level(self) -> None:
        if self._pump:
            self._pump.cancel()
            self._pump = None

    async def _level_loop(self, source) -> None:
        try:
            while True:
                await self.set(level=round(float(source.level), 3))
                await asyncio.sleep(0.05)  # 20 fps is plenty for a waveform
        except asyncio.CancelledError:
            pass
