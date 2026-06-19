from __future__ import annotations

from pathlib import Path

from bastion_ui.app import PUBLIC_ROUTE_REGISTRATIONS
from bastion_ui.components.evidence.proof_packet_viewer import proof_packet_viewer


def test_proof_packet_route_exists() -> None:
    routes = {route for route, _, _ in PUBLIC_ROUTE_REGISTRATIONS}
    assert "/trace/[report_id]/proof-packet" in routes
    assert proof_packet_viewer is not None


def test_missing_proof_packet_state_is_safe() -> None:
    source = (
        Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("components/evidence/proof_packet_viewer.py")
        .read_text()
    )
    assert "Proof Packet unavailable" in source
    assert "does not fake" not in source.casefold()
    assert "endpoint may not be exposed" in source
