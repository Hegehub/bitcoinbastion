from dataclasses import replace

from app.services.bastion_trace.evidence_workflow import TraceEvidenceWorkflowService
from app.services.bastion_trace.proof_packet import TraceProofPacketAssembler
from tests.services.bastion_trace.test_trace_proof_packet import _graph


def _packet(snapshot_id: str = "trace_snapshot:a", relationship_id: str = "relationship:a"):
    return TraceProofPacketAssembler().assemble(
        trace_id=1,
        subject="bc1q",
        claim_capture_id="trace_report:1",
        graph=_graph(snapshot_id, relationship_id),
        claims=(),
        disagreements=(),
        historical=True,
    )


def test_lineage_is_typed_directed_bounded_and_branched() -> None:
    packet = _packet()
    evidence_id = packet.evidence[0].evidence_id
    lineage = TraceEvidenceWorkflowService().lineage(packet, evidence_id)
    assert lineage.evidence.evidence_id == evidence_id
    assert lineage.graph_snapshot_id == "trace_snapshot:a"
    assert lineage.completeness.value == "complete"
    assert {node.kind.value for node in lineage.nodes} >= {
        "source_reference",
        "evidence",
        "topology_relationship",
        "graph_snapshot",
        "proof_packet",
    }
    assert {edge.relation.value for edge in lineage.edges} >= {
        "produced_from",
        "supports",
        "captured_in",
        "included_in",
    }
    assert all(edge.direction == "directed" for edge in lineage.edges)
    assert len(lineage.nodes) <= 8
    assert len(lineage.paths) >= 2


def test_replay_match_and_scoped_verification_do_not_claim_analytical_truth() -> None:
    packet = _packet()
    evidence_id = packet.evidence[0].evidence_id
    service = TraceEvidenceWorkflowService()
    first = service.replay(packet, evidence_id)
    second = service.replay(packet, evidence_id)
    assert first.status.value == second.status.value == "match"
    assert first.reproduced_identity == evidence_id
    assert first.method_version == "trace-evidence-identity-v1"
    verification = service.verification(packet, evidence_id)
    assert verification.status.value == "verified"
    assert verification.scope.value == "evidence_identity_integrity"
    assert "analytical conclusions" in " ".join(verification.limitations)


def test_legitimate_forged_identity_fixture_returns_typed_mismatch_without_mutation() -> None:
    packet = _packet()
    original = packet.evidence[0]
    forged = replace(original, evidence_id="trace_evidence:forged-integration-fixture")
    fixture = replace(packet, evidence=(forged,))
    replay = TraceEvidenceWorkflowService().replay(fixture, forged.evidence_id)
    assert replay.status.value == "mismatch"
    assert replay.original_identity == forged.evidence_id
    assert replay.reproduced_identity != forged.evidence_id
    assert packet.evidence[0] == original


def test_historical_lineage_and_replay_use_exact_snapshot_inputs() -> None:
    packet_a = _packet("trace_snapshot:a", "relationship:a")
    packet_b = _packet("trace_snapshot:b", "relationship:b")
    service = TraceEvidenceWorkflowService()
    evidence_a = packet_a.evidence[0].evidence_id
    lineage_a = service.lineage(packet_a, evidence_a)
    replay_a = service.replay(packet_a, evidence_a)
    assert lineage_a.graph_snapshot_id == "trace_snapshot:a"
    assert "relationship:b" not in lineage_a.model_dump_json()
    assert replay_a.immutable_input_ids[-1] == "trace_snapshot:a"
    assert packet_b.evidence[0].evidence_id not in lineage_a.model_dump_json()


def test_backend_json_export_is_safe_versioned_and_identity_bound() -> None:
    packet = _packet()
    evidence_id = packet.evidence[0].evidence_id
    exported = TraceEvidenceWorkflowService().export(packet, evidence_id)
    assert exported.schema_version == "trace-evidence-export-v1"
    assert exported.evidence_id == evidence_id
    assert exported.graph_snapshot_id == "trace_snapshot:a"
    assert exported.media_type == "application/json"
    assert exported.filename.endswith(".json")
    assert exported.content_digest not in exported.content
    assert "TRACE_EVIDENCE_LINEAGE_PRIVACY_CANARY_NEVER_BROWSER" not in exported.content
    assert "private_provider_token" not in exported.content
