from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.services.events.websocket_contracts import WIRE_FRAME_ADAPTER, WIRE_PROTOCOL_VERSION
from app.services.events.websocket_registry import WEBSOCKET_CONTRACTS
from app.services.events.websocket_serialization import heartbeat_message, system_message


def test_all_nine_routes_have_authoritative_versions_and_unique_owners() -> None:
    assert len(WEBSOCKET_CONTRACTS) == 9
    assert [item.blocker_id for item in WEBSOCKET_CONTRACTS] == [
        f"P1R2-B{i:02d}" for i in range(5, 14)
    ]
    assert len({item.route for item in WEBSOCKET_CONTRACTS}) == 9
    assert all(item.wire_version == WIRE_PROTOCOL_VERSION for item in WEBSOCKET_CONTRACTS)
    assert all(
        item.frontend_owner == "bastion_ui.realtime.transport:WebSocketTransport"
        for item in WEBSOCKET_CONTRACTS
    )
    assert all(item.max_buffered_frames == 128 for item in WEBSOCKET_CONTRACTS)


def test_system_and_heartbeat_frames_strictly_validate() -> None:
    accepted = system_message(
        "connection.accepted",
        "Connected",
        stream="provider-health",
        topics=["provider-health"],
        event_types=None,
    )
    assert WIRE_FRAME_ADAPTER.validate_json(json.dumps(accepted)).wire_version == 1
    assert WIRE_FRAME_ADAPTER.validate_json(json.dumps(heartbeat_message())).type == "heartbeat"


def test_unknown_version_and_malformed_payload_fail_closed() -> None:
    invalid = heartbeat_message() | {"wire_version": 99}
    with pytest.raises(ValidationError):
        WIRE_FRAME_ADAPTER.validate_json(json.dumps(invalid))
    with pytest.raises(ValidationError):
        WIRE_FRAME_ADAPTER.validate_json('{"type":"event"}')
