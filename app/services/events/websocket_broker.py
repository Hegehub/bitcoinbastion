from __future__ import annotations

from dataclasses import dataclass
import asyncio
from uuid import uuid4

from fastapi import WebSocket
from app.core import telemetry
from app.db.models.event_outbox import EventOutbox
from app.services.events.websocket_filters import should_deliver
from app.services.events.websocket_serialization import heartbeat_message, serialize_outbox_event


@dataclass
class WebSocketConnection:
    websocket: WebSocket
    topics: set[str]
    limit_payload: bool = True
    event_types: set[str] | None = None


class WebSocketBroker:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocketConnection] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        topics: set[str],
        *,
        limit_payload: bool = True,
        event_types: set[str] | None = None,
    ) -> str:
        await websocket.accept()
        connection_id = f"wsc_{uuid4().hex}"
        async with self._lock:
            self._connections[connection_id] = WebSocketConnection(
                websocket=websocket,
                topics=set(topics),
                limit_payload=limit_payload,
                event_types=set(event_types) if event_types is not None else None,
            )
            telemetry.BASTION_WS_CONNECTIONS_ACTIVE.set(len(self._connections))
            telemetry.BASTION_WS_CONNECTIONS_TOTAL.inc()
        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        async with self._lock:
            self._connections.pop(connection_id, None)
            telemetry.BASTION_WS_CONNECTIONS_ACTIVE.set(len(self._connections))

    async def broadcast_event(self, event: dict[str, object]) -> None:
        event_type = str(event.get("event_type", ""))
        stale: list[str] = []
        async with self._lock:
            connections = list(self._connections.items())
        for connection_id, connection in connections:
            if connection.event_types is not None and event_type not in connection.event_types:
                continue
            if not should_deliver(event_type, connection.topics):
                continue
            try:
                await connection.websocket.send_json(event)
                telemetry.BASTION_WS_MESSAGES_SENT_TOTAL.labels(message_type="event").inc()
            except Exception:
                telemetry.BASTION_WS_SEND_FAILURES_TOTAL.labels(reason="send_error").inc()
                stale.append(connection_id)
        for connection_id in stale:
            await self.disconnect(connection_id)

    async def broadcast_outbox_event(self, event: EventOutbox) -> None:
        message = serialize_outbox_event(event)
        await self.broadcast_event(message)

    async def send_heartbeat(self, connection_id: str) -> None:
        async with self._lock:
            connection = self._connections.get(connection_id)
        if connection is None:
            return
        try:
            await connection.websocket.send_json(heartbeat_message())
            telemetry.BASTION_WS_HEARTBEAT_TOTAL.inc()
            telemetry.BASTION_WS_MESSAGES_SENT_TOTAL.labels(message_type="heartbeat").inc()
        except Exception:
            telemetry.BASTION_WS_SEND_FAILURES_TOTAL.labels(reason="heartbeat_error").inc()
            await self.disconnect(connection_id)

    def active_connection_count(self) -> int:
        return len(self._connections)


websocket_broker = WebSocketBroker()
