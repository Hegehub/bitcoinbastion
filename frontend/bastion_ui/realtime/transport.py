from __future__ import annotations

import asyncio
from collections import deque
from enum import StrEnum
from typing import Any

from pydantic import ValidationError
from websockets.asyncio.client import connect

from bastion_ui.realtime.contracts import EventFrame, Frame, decode_frame


class ConnectionStatus(StrEnum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    UNAUTHORIZED = "UNAUTHORIZED"
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"
    FAILED = "FAILED"


class WebSocketTransport:
    """Single bounded frame/lifecycle owner; domain interpretation stays outside."""

    def __init__(self, *, recent_id_limit: int = 128, maximum_reconnects: int = 5) -> None:
        self.status = ConnectionStatus.DISCONNECTED
        self.maximum_reconnects = maximum_reconnects
        self._recent_ids: deque[str] = deque(maxlen=recent_id_limit)
        self._connection_active = False
        self._socket: Any | None = None

    def begin_connect(self) -> None:
        if self._connection_active:
            raise RuntimeError("duplicate_websocket_connection")
        self._connection_active = True
        self.status = ConnectionStatus.CONNECTING

    def connected(self) -> None:
        self.status = ConnectionStatus.CONNECTED

    def disconnect(self, *, offline: bool = False) -> None:
        self._connection_active = False
        self.status = ConnectionStatus.OFFLINE if offline else ConnectionStatus.DISCONNECTED

    def decode(self, raw: str | bytes) -> Frame | None:
        try:
            frame = decode_frame(raw)
        except ValidationError as exc:
            text = raw.decode() if isinstance(raw, bytes) else raw
            self.status = (
                ConnectionStatus.UNSUPPORTED_VERSION
                if '"wire_version"' in text
                else ConnectionStatus.FAILED
            )
            raise ValueError("invalid_websocket_frame") from exc
        if isinstance(frame, EventFrame):
            if frame.event_id in self._recent_ids:
                return None
            self._recent_ids.append(frame.event_id)
        return frame

    @staticmethod
    def reconnect_delay(attempt: int) -> float:
        if attempt < 0:
            raise ValueError("negative_reconnect_attempt")
        return float(min(30.0, 0.5 * (2**attempt)))

    def may_reconnect(self, attempt: int) -> bool:
        return (
            self.status not in {ConnectionStatus.UNAUTHORIZED, ConnectionStatus.UNSUPPORTED_VERSION}
            and attempt < self.maximum_reconnects
        )

    async def receive_first(self, uri: str) -> Frame | None:
        self.begin_connect()
        try:
            socket = await connect(uri)
            self._socket = socket
            frame = self.decode(await asyncio.wait_for(socket.recv(), timeout=5.0))
            self.connected()
            return frame
        except Exception:
            await self.close()
            raise

    async def close(self) -> None:
        """Close the owned socket before disabling reconnect eligibility."""
        socket, self._socket = self._socket, None
        if socket is not None:
            await socket.close()
        self.disconnect()

    def visibility_changed(self, *, visible: bool) -> None:
        if not visible:
            self.disconnect()
        elif self.status is ConnectionStatus.DISCONNECTED:
            self.status = ConnectionStatus.RECONNECTING

    def network_changed(self, *, online: bool) -> None:
        if not online:
            self.disconnect(offline=True)
        elif self.status is ConnectionStatus.OFFLINE:
            self.status = ConnectionStatus.RECONNECTING
