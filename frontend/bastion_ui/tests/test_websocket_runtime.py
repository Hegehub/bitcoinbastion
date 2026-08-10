from __future__ import annotations

from bastion_ui.domain.provenance import ProvenanceState
from bastion_ui.realtime.contracts import SystemFrame
from bastion_ui.realtime.degraded_lab import run_scenario
from bastion_ui.realtime.fixtures import PROVIDER_HEALTH_FIXTURES, fixture
from bastion_ui.realtime.transport import ConnectionStatus, WebSocketTransport


def test_fixture_library_is_deterministic_safe_and_demo_only() -> None:
    assert fixture("normal") == fixture("normal")
    assert all(
        item.expected_provenance is ProvenanceState.DEMO_FIXTURE
        for item in PROVIDER_HEALTH_FIXTURES
    )
    serialized = str(PROVIDER_HEALTH_FIXTURES).lower()
    for secret in ("private_key", "session_secret", "payment_proof", "mnemonic"):
        assert secret not in serialized


def test_transport_strict_decode_and_duplicate_connection_prevention() -> None:
    transport = WebSocketTransport()
    transport.begin_connect()
    try:
        transport.begin_connect()
    except RuntimeError as error:
        assert str(error) == "duplicate_websocket_connection"
    frame = transport.decode(fixture("normal").payload_json)
    assert isinstance(frame, SystemFrame)
    transport.connected()
    assert transport.status is ConnectionStatus.CONNECTED


def test_unsupported_and_malformed_frames_fail_without_state_payload() -> None:
    assert run_scenario("unsupported-version").status is ConnectionStatus.UNSUPPORTED_VERSION
    assert run_scenario("malformed").status is ConnectionStatus.FAILED


def test_backoff_is_bounded_and_permanent_failures_stop_reconnect() -> None:
    transport = WebSocketTransport(maximum_reconnects=5)
    assert [transport.reconnect_delay(i) for i in range(8)] == [
        0.5,
        1.0,
        2.0,
        4.0,
        8.0,
        16.0,
        30.0,
        30.0,
    ]
    transport.status = ConnectionStatus.UNSUPPORTED_VERSION
    assert not transport.may_reconnect(0)


def test_disconnect_and_offline_status_are_explicit() -> None:
    def status_value(value: WebSocketTransport) -> str:
        return value.status.value

    transport = WebSocketTransport()
    transport.begin_connect()
    transport.disconnect(offline=True)
    assert status_value(transport) == "OFFLINE"
    transport.network_changed(online=True)
    assert status_value(transport) == "RECONNECTING"
    transport.visibility_changed(visible=False)
    assert status_value(transport) == "DISCONNECTED"
