from datetime import UTC, datetime
from pathlib import Path

from bastion_ui.domain.prompt14 import adapt_trace_proof_packet
from bastion_ui.domain.prompt14_scenarios import PROMPT14_SCENARIOS
from bastion_ui.domain.provenance import ProvenanceState
from bastion_ui.topology import ROUTE_BY_ID, RouteClass
from bastion_ui.transport.generated_schemas import SafeTraceProofPacketDTO


def _packet() -> SafeTraceProofPacketDTO:
    return SafeTraceProofPacketDTO.model_validate(
        {
            "packet_id": "trace_proof_packet:1",
            "packet_schema_version": "trace-proof-packet-v1",
            "assembler_version": "trace-proof-packet-assembler-v1",
            "trace_id": 1,
            "graph_snapshot_id": "trace_snapshot:a",
            "claim_capture_id": "trace_report:1",
            "subject": "bc1qexample",
            "captured_at": datetime(2026, 8, 15, tzinfo=UTC),
            "historical": False,
            "topology": {
                "graph_snapshot_id": "trace_snapshot:a",
                "topology_snapshot_id": "topology:a",
                "node_ids": ["address:1", "transaction:1"],
                "relationship_ids": ["relationship:1"],
            },
            "claims": [],
            "disagreements": [],
            "evidence": [
                {
                    "evidence_id": "trace_evidence:1",
                    "kind": "topology_relationship_support",
                    "reference": "observation:1",
                    "producer": "bitcoin-topology-adapter",
                    "source_category": "public_chain",
                    "captured_at": datetime(2026, 8, 15, tzinfo=UTC),
                    "linked_claim_ids": [],
                    "linked_relationship_ids": ["relationship:1"],
                    "integrity_status": "not_checked",
                    "verification_status": "not_verified",
                    "limitations": [],
                }
            ],
            "packet_digest": "digest",
            "integrity_status": "content_integrity_checked",
            "verification_status": "not_verified",
            "advisory_only": True,
            "not_legal_verification": True,
            "not_bitcoin_consensus_proof": True,
            "limitations": ["Evidence linkage does not mean independent verification."],
        }
    )


def test_feature54_preserves_packet_membership_and_verification_posture() -> None:
    view = adapt_trace_proof_packet(_packet())
    assert view.packet_id == "trace_proof_packet:1"
    assert view.graph_snapshot_id == "trace_snapshot:a"
    assert view.verification_status == "not_verified"
    assert view.integrity_status == "content_integrity_checked"
    assert view.evidence[0].linked_relationship_ids == ("relationship:1",)


def test_components_never_assemble_packet_or_consume_raw_transport() -> None:
    component = Path("bastion_ui/components/evidence/proof_packet_viewer.py").read_text()
    state = Path("bastion_ui/state/trace_proof_packet_state.py").read_text()
    assert "generated_schemas" not in component
    assert "generated_http" not in component
    assert "dict[str" not in state
    assert "token != self.generation" in state
    assert "TRACE_EVIDENCE_PRIVACY_CANARY_NEVER_BROWSER" not in component + state
    assert "sha256" not in component + state
    assert 'id="trace-proof-packet"' in component
    assert "evidence-trigger-" in component + state
    assert "document.getElementById" in state
    assert "high_contrast=True" in component


def test_packet_routes_and_degraded_scenarios_have_canonical_ownership() -> None:
    current = ROUTE_BY_ID["trace.proof_packet"]
    historical = ROUTE_BY_ID["trace.historical_proof_packet"]
    assert current.route_class is RouteClass.PROTECTED
    assert current.http_operations[0] == "get_current_trace_proof_packet"
    assert historical.http_operations[0] == "get_historical_trace_proof_packet"
    assert "get_trace_evidence_lineage" in current.http_operations
    assert "export_trace_evidence" in historical.http_operations
    assert historical.path.endswith("/history/[snapshot_id]/proof-packet")
    assert all(item.provenance is ProvenanceState.DEMO_FIXTURE for item in PROMPT14_SCENARIOS)
