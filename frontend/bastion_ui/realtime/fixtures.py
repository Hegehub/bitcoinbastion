from __future__ import annotations

import json
from dataclasses import dataclass

from bastion_ui.domain.provenance import ProvenanceState


@dataclass(frozen=True)
class WireFixture:
    family: str
    wire_version: int
    scenario_id: str
    payload_json: str
    expected_provenance: ProvenanceState
    expected_status: str


def _json(value: dict[str, object]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


PROVIDER_HEALTH_FIXTURES = (
    WireFixture(
        "provider-health",
        1,
        "normal",
        _json(
            {
                "protocol": "bitcoin-bastion.events",
                "wire_version": 1,
                "type": "system",
                "event_type": "connection.accepted",
                "message": "Connected to deterministic provider health fixture.",
                "stream": "provider-health",
                "topics": ["provider-health"],
                "event_types": None,
                "last_event_id": None,
            }
        ),
        ProvenanceState.DEMO_FIXTURE,
        "CONNECTED",
    ),
    WireFixture(
        "provider-health",
        1,
        "malformed",
        '{"type":"event"}',
        ProvenanceState.DEMO_FIXTURE,
        "FAILED",
    ),
    WireFixture(
        "provider-health",
        99,
        "unsupported-version",
        '{"protocol":"bitcoin-bastion.events","wire_version":99,"type":"heartbeat","event_type":"heartbeat","timestamp":"2026-08-10T00:00:00Z"}',
        ProvenanceState.DEMO_FIXTURE,
        "UNSUPPORTED_VERSION",
    ),
)


def fixture(scenario_id: str) -> WireFixture:
    return next(item for item in PROVIDER_HEALTH_FIXTURES if item.scenario_id == scenario_id)
