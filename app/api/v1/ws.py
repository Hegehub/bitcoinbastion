from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query, WebSocket

from app.core import telemetry
from app.services.events.websocket_broker import websocket_broker
from app.services.events.websocket_filters import (
    SUPPORTED_TOPICS,
    WebSocketTopicError,
    parse_topics,
    stream_event_types,
    stream_topics,
)
from app.services.events.websocket_serialization import error_message, system_message

router = APIRouter(tags=["websockets"])


def _parse_bool(value: str | None, *, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().casefold() not in {"0", "false", "no", "off"}


def _heartbeat_seconds(value: int | None) -> int:
    if value is None:
        return 30
    return max(10, min(value, 120))


async def _heartbeat_loop(connection_id: str, heartbeat_delay: int) -> None:
    try:
        while True:
            await asyncio.sleep(heartbeat_delay)
            await websocket_broker.send_heartbeat(connection_id)
    except Exception:
        await websocket_broker.disconnect(connection_id)


async def _connect_stream(
    websocket: WebSocket,
    *,
    subscribed_topics: set[str],
    stream_name: str,
    limit_payload: str | None,
    heartbeat_seconds: int | None,
    event_types: set[str] | None = None,
    last_event_id: str | None = None,
) -> None:
    connection_id = await websocket_broker.connect(
        websocket,
        subscribed_topics,
        limit_payload=_parse_bool(limit_payload),
        event_types=event_types,
    )
    await websocket.send_json(
        system_message(
            "connection.accepted",
            "Connected to Bitcoin Bastion event stream.",
            stream=stream_name,
            topics=sorted(subscribed_topics),
            event_types=sorted(event_types) if event_types is not None else None,
        )
    )
    if last_event_id:
        await websocket.send_json(
            system_message(
                "replay.not_available",
                "last_event_id replay is not available in this build.",
                last_event_id=last_event_id,
            )
        )
    await _heartbeat_loop(connection_id, _heartbeat_seconds(heartbeat_seconds))


@router.websocket("/ws/events")
async def ws_events(
    websocket: WebSocket,
    topics: str | None = Query(default=None),
    limit_payload: str | None = Query(default="true"),
    heartbeat_seconds: int | None = Query(default=30),
    last_event_id: str | None = Query(default=None),
) -> None:
    try:
        subscribed_topics = parse_topics(topics)
    except WebSocketTopicError:
        telemetry.BASTION_WS_INVALID_SUBSCRIPTION_TOTAL.inc()
        await websocket.accept()
        await websocket.send_json(
            error_message(
                "One or more requested topics are not supported.",
                supported_topics=sorted(SUPPORTED_TOPICS),
            )
        )
        await websocket.close(code=1008)
        return

    await _connect_stream(
        websocket,
        subscribed_topics=subscribed_topics,
        stream_name="events",
        limit_payload=limit_payload,
        heartbeat_seconds=heartbeat_seconds,
        last_event_id=last_event_id,
    )


async def _specialized_stream(
    websocket: WebSocket,
    *,
    stream_name: str,
    limit_payload: str | None,
    heartbeat_seconds: int | None,
) -> None:
    event_types = set(stream_event_types(stream_name))
    await _connect_stream(
        websocket,
        subscribed_topics=stream_topics(stream_name),
        stream_name=stream_name,
        limit_payload=limit_payload,
        heartbeat_seconds=heartbeat_seconds,
        event_types=event_types,
    )


@router.websocket("/ws/signals")
async def ws_signals(
    websocket: WebSocket,
    limit_payload: str | None = Query(default="true"),
    heartbeat_seconds: int | None = Query(default=30),
) -> None:
    await _specialized_stream(
        websocket, stream_name="signals", limit_payload=limit_payload, heartbeat_seconds=heartbeat_seconds
    )


@router.websocket("/ws/news")
async def ws_news(
    websocket: WebSocket,
    limit_payload: str | None = Query(default="true"),
    heartbeat_seconds: int | None = Query(default=30),
) -> None:
    await _specialized_stream(websocket, stream_name="news", limit_payload=limit_payload, heartbeat_seconds=heartbeat_seconds)


@router.websocket("/ws/onchain")
async def ws_onchain(
    websocket: WebSocket,
    limit_payload: str | None = Query(default="true"),
    heartbeat_seconds: int | None = Query(default=30),
) -> None:
    await _specialized_stream(
        websocket, stream_name="onchain", limit_payload=limit_payload, heartbeat_seconds=heartbeat_seconds
    )


@router.websocket("/ws/market")
async def ws_market(
    websocket: WebSocket,
    limit_payload: str | None = Query(default="true"),
    heartbeat_seconds: int | None = Query(default=30),
) -> None:
    await _specialized_stream(websocket, stream_name="market", limit_payload=limit_payload, heartbeat_seconds=heartbeat_seconds)


@router.websocket("/ws/trace")
async def ws_trace(
    websocket: WebSocket,
    limit_payload: str | None = Query(default="true"),
    heartbeat_seconds: int | None = Query(default=30),
) -> None:
    await _specialized_stream(websocket, stream_name="trace", limit_payload=limit_payload, heartbeat_seconds=heartbeat_seconds)


@router.websocket("/ws/treasury")
async def ws_treasury(
    websocket: WebSocket,
    limit_payload: str | None = Query(default="true"),
    heartbeat_seconds: int | None = Query(default=30),
) -> None:
    await _specialized_stream(
        websocket, stream_name="treasury", limit_payload=limit_payload, heartbeat_seconds=heartbeat_seconds
    )


@router.websocket("/ws/provider-health")
async def ws_provider_health(
    websocket: WebSocket,
    limit_payload: str | None = Query(default="true"),
    heartbeat_seconds: int | None = Query(default=30),
) -> None:
    await _specialized_stream(
        websocket, stream_name="provider-health", limit_payload=limit_payload, heartbeat_seconds=heartbeat_seconds
    )


@router.websocket("/ws/intelligence-timeline")
async def ws_intelligence_timeline(
    websocket: WebSocket,
    limit_payload: str | None = Query(default="true"),
    heartbeat_seconds: int | None = Query(default=30),
) -> None:
    await _specialized_stream(
        websocket,
        stream_name="intelligence-timeline",
        limit_payload=limit_payload,
        heartbeat_seconds=heartbeat_seconds,
    )
