from __future__ import annotations

from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any, Self
from urllib.parse import urlencode, urlparse, urlunparse

import websockets

from bitcoin_bastion_sdk.config import BastionSDKConfig
from bitcoin_bastion_sdk.errors import BastionWebSocketError

SPECIALIZED_STREAMS = {
    "signals",
    "news",
    "onchain",
    "market",
    "trace",
    "treasury",
    "provider-health",
    "intelligence-timeline",
}


def websocket_url(base_url: str, api_prefix: str, path: str, params: dict[str, Any] | None = None) -> str:
    config = BastionSDKConfig(base_url=base_url, api_prefix=api_prefix)
    parsed = urlparse(config.base_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    query = urlencode({key: value for key, value in (params or {}).items() if value is not None}, doseq=True)
    return urlunparse((scheme, parsed.netloc, f"{config.api_prefix}{path}", "", query, ""))


class WebSocketStream:
    def __init__(self, url: str, headers: dict[str, str] | None = None) -> None:
        self.url = url
        self.headers = headers or {}
        self._connection: Any | None = None

    async def __aenter__(self) -> Self:
        self._connection = await websockets.connect(self.url, additional_headers=self.headers)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._connection is not None:
            await self._connection.close()

    def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[dict[str, Any]]:
        if self._connection is None:
            async with self:
                async for item in self._iterate_open():
                    yield item
            return
        async for item in self._iterate_open():
            yield item

    async def _iterate_open(self) -> AsyncIterator[dict[str, Any]]:
        if self._connection is None:
            raise BastionWebSocketError("WebSocket stream is not connected")
        async for message in self._connection:
            import json

            parsed = json.loads(message)
            if isinstance(parsed, dict):
                yield parsed


class WebSocketClient:
    def __init__(self, *, base_url: str, api_prefix: str, headers: dict[str, str] | None = None) -> None:
        self.base_url = base_url
        self.api_prefix = api_prefix
        self.headers = headers or {}

    def subscribe_events(self, *, topics: list[str] | None = None, heartbeat_seconds: int | None = None) -> WebSocketStream:
        params: dict[str, Any] = {}
        if topics:
            params["topics"] = ",".join(topics)
        if heartbeat_seconds is not None:
            params["heartbeat_seconds"] = heartbeat_seconds
        return WebSocketStream(websocket_url(self.base_url, self.api_prefix, "/ws/events", params), self.headers)

    def subscribe(self, stream: str, *, heartbeat_seconds: int | None = None) -> WebSocketStream:
        normalized = stream.strip().casefold()
        if normalized not in SPECIALIZED_STREAMS:
            raise BastionWebSocketError(f"Unsupported WebSocket stream: {stream}")
        params = {"heartbeat_seconds": heartbeat_seconds} if heartbeat_seconds is not None else None
        return WebSocketStream(websocket_url(self.base_url, self.api_prefix, f"/ws/{normalized}", params), self.headers)
