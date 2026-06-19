from __future__ import annotations

from pathlib import Path

from bastion_ui.components.trace.proof_packet_viewer import proof_packet_viewer
from bastion_ui.routes.proof_packet import trace_proof_packet_page


def test_proof_packet_route_imports() -> None:
    assert trace_proof_packet_page is not None
    assert proof_packet_viewer is not None


def test_proof_packet_unavailable_copy_does_not_fake_hashes() -> None:
    source = (
        Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("components/trace/proof_packet_viewer.py")
        .read_text()
    )
    assert "Proof packet is not available for this report." in source
    assert "No placeholder hashes or fabricated packet metadata are shown." in source
    assert "000000" not in source
    assert "abcdef" not in source.lower()
