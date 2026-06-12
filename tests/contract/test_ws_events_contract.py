from fastapi.testclient import TestClient

from app.main import app
from app.services.events.websocket_serialization import serialize_event_payload

FORBIDDEN_WORDING = (
    "clean address",
    "dirty address",
    "criminal address",
    "guaranteed safe",
    "approved payment",
    "verified illicit",
)


def test_ws_events_accepts_connection_and_sends_system_message() -> None:
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/events?topics=signals,trace") as websocket:
        message = websocket.receive_json()

    assert message["type"] == "system"
    assert message["event_type"] == "connection.accepted"
    assert message["topics"] == ["signals", "trace"]


def test_ws_events_invalid_topic_returns_error_envelope() -> None:
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/events?topics=signals,unknown") as websocket:
        message = websocket.receive_json()

    assert message["type"] == "error"
    assert message["event_type"] == "subscription.invalid"
    assert "signals" in message["supported_topics"]


def test_ws_events_last_event_id_reports_replay_unavailable() -> None:
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/events?last_event_id=evt_1") as websocket:
        accepted = websocket.receive_json()
        replay = websocket.receive_json()

    assert accepted["event_type"] == "connection.accepted"
    assert replay["event_type"] == "replay.not_available"


def test_event_envelope_stable_keys_and_redacts_sensitive_material() -> None:
    envelope = serialize_event_payload(
        event_id="evt_1",
        event_type="trace.report.created",
        domain="trace",
        version=1,
        occurred_at=None,
        payload={
            "report_id": 1,
            "authorization": "bearer token example",
            "degraded": True,
            "stale": True,
            "fallback": True,
        },
    )

    assert {
        "type",
        "event_id",
        "event_type",
        "domain",
        "topic",
        "version",
        "occurred_at",
        "published_at",
        "data",
        "limitations",
        "degraded",
        "stale",
        "payload",
        "metadata",
    } <= set(envelope)
    assert envelope["topic"] == "trace"
    assert envelope["data"]["authorization"] == "[REDACTED]"
    assert envelope["payload"]["authorization"] == "[REDACTED]"
    assert envelope["metadata"]["redacted"] is True
    assert envelope["metadata"]["degraded"] is True
    assert envelope["metadata"]["stale"] is True
    assert envelope["degraded"] is True
    assert envelope["stale"] is True
    assert envelope["metadata"]["fallback"] is True
    assert envelope["metadata"]["no_custody"] is True


def test_forbidden_trace_wording_absent() -> None:
    checked = " ".join(
        [
            "Connected to Bitcoin Bastion event stream.",
            "One or more requested topics are not supported.",
            "last_event_id replay is not available in this build.",
        ]
    ).casefold()
    for phrase in FORBIDDEN_WORDING:
        assert phrase not in checked
