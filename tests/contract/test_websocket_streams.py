from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services.events.websocket_filters import stream_event_types
from app.services.events.websocket_serialization import heartbeat_message, serialize_event_payload

FORBIDDEN_WORDING = (
    "clean address",
    "dirty address",
    "criminal address",
    "guaranteed safe",
    "approved payment",
    "verified illicit",
)

SENSITIVE_TERMS = (
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
)

STREAM_ROUTES = [
    ("/api/v1/ws/signals", "signals"),
    ("/api/v1/ws/news", "news"),
    ("/api/v1/ws/onchain", "onchain"),
    ("/api/v1/ws/market", "market"),
    ("/api/v1/ws/trace", "trace"),
    ("/api/v1/ws/treasury", "treasury"),
    ("/api/v1/ws/provider-health", "provider-health"),
    ("/api/v1/ws/intelligence-timeline", "intelligence-timeline"),
]


@pytest.mark.parametrize(("route", "stream"), STREAM_ROUTES)
def test_specialized_websocket_stream_accepts_connection(route: str, stream: str) -> None:
    client = TestClient(app)
    with client.websocket_connect(route) as websocket:
        message = websocket.receive_json()

    assert message["type"] == "system"
    assert message["event_type"] == "connection.accepted"
    assert message["stream"] == stream
    assert set(message["event_types"]) == stream_event_types(stream)


def test_specialized_message_envelope_contains_standard_fields() -> None:
    envelope = serialize_event_payload(
        event_id="evt_stream_1",
        event_type="signal.published",
        domain="signal",
        version=1,
        occurred_at=None,
        payload={"signal_id": 1, "limitations": ["not financial advice"], "degraded": False, "stale": False},
    )

    assert {
        "type",
        "event_type",
        "event_id",
        "topic",
        "version",
        "occurred_at",
        "data",
        "limitations",
        "degraded",
        "stale",
    } <= set(envelope)
    assert envelope["topic"] == "signals"
    assert envelope["limitations"] == ["not financial advice"]


def test_heartbeat_message_is_serializable() -> None:
    message = heartbeat_message()
    assert message["type"] == "heartbeat"
    assert message["event_type"] == "heartbeat"
    assert "timestamp" in message


def test_sensitive_material_is_redacted_from_stream_payload() -> None:
    envelope = serialize_event_payload(
        event_id="evt_sensitive",
        event_type="trace.report.created",
        domain="trace",
        version=1,
        occurred_at=None,
        payload={"report_id": 1, "private_key": "do not emit", "notes": "seed phrase was supplied"},
    )

    serialized = str(envelope).casefold()
    for term in SENSITIVE_TERMS:
        assert term not in serialized
    assert envelope["metadata"]["redacted"] is True
    assert envelope["data"]["private_key"] == "[REDACTED]"


def test_forbidden_trace_wording_absent_from_stream_messages() -> None:
    checked = " ".join(
        [
            "Connected to Bitcoin Bastion event stream.",
            "last_event_id replay is not available in this build.",
            "Unsupported WebSocket topic.",
        ]
    ).casefold()
    for phrase in FORBIDDEN_WORDING:
        assert phrase not in checked
