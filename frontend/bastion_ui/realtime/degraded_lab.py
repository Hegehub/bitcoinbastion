from __future__ import annotations

from dataclasses import dataclass

from bastion_ui.realtime.fixtures import WireFixture, fixture
from bastion_ui.realtime.transport import ConnectionStatus, WebSocketTransport


@dataclass(frozen=True)
class LabResult:
    scenario_id: str
    status: ConnectionStatus
    demo_only: bool = True


def run_scenario(scenario_id: str) -> LabResult:
    selected: WireFixture = fixture(scenario_id)
    transport = WebSocketTransport()
    transport.begin_connect()
    try:
        transport.decode(selected.payload_json)
        transport.connected()
    except ValueError:
        pass
    return LabResult(scenario_id, transport.status)
