import pytest

from app.services.events.websocket_filters import (
    MAX_TOPICS_PER_CONNECTION,
    WebSocketTopicError,
    parse_topics,
)
from app.services.events.websocket_serialization import serialize_event_payload


def test_too_many_explicit_websocket_topics_rejected() -> None:
    topics = ",".join(
        [
            "signals",
            "trace",
            "market",
            "news",
            "onchain",
            "treasury",
            "policy",
            "wallet",
            "evidence",
        ][: MAX_TOPICS_PER_CONNECTION + 1]
    )
    with pytest.raises(WebSocketTopicError):
        parse_topics(topics)


def test_websocket_payload_sanitizes_sensitive_material_and_limits_large_payload() -> None:
    message = serialize_event_payload(
        event_id="evt_1",
        event_type="signal.published",
        domain="signal",
        version=1,
        occurred_at=None,
        payload={"secret": "private key must be hidden", "large": "x" * (20 * 1024)},
    )
    assert message["metadata"]["redacted"] is True
    assert message["payload"] == {"truncated": True, "reason": "payload_size_limit"}
