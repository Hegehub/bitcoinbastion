from __future__ import annotations

import pytest

from bitcoin_bastion_sdk.errors import BastionWebSocketError
from bitcoin_bastion_sdk.websocket import WebSocketClient, websocket_url


def test_builds_ws_events_url_correctly() -> None:
    url = websocket_url("http://localhost:8000", "/api/v1", "/ws/events", {"topics": "signals,trace"})
    assert url == "ws://localhost:8000/api/v1/ws/events?topics=signals%2Ctrace"


def test_supports_topic_query() -> None:
    client = WebSocketClient(base_url="https://example.com", api_prefix="/api/v1")
    stream = client.subscribe_events(topics=["signals", "trace"])
    assert stream.url == "wss://example.com/api/v1/ws/events?topics=signals%2Ctrace"


def test_maps_specialized_stream_names_safely() -> None:
    client = WebSocketClient(base_url="http://localhost:8000", api_prefix="/api/v1")
    assert client.subscribe("provider-health").url == "ws://localhost:8000/api/v1/ws/provider-health"


def test_does_not_fake_missing_streams() -> None:
    client = WebSocketClient(base_url="http://localhost:8000", api_prefix="/api/v1")
    with pytest.raises(BastionWebSocketError):
        client.subscribe("wallet")
