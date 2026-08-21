from datetime import UTC, datetime

from app.schemas.trace_graph import (
    TraceGraphApiVersion,
    TraceGraphDTO,
    TraceGraphEvidenceReferenceDTO,
    TraceGraphMetadataDTO,
    TraceGraphObjectDTO,
    TraceGraphProvenanceDTO,
    TraceGraphRelationshipDTO,
    TraceGraphSnapshotDTO,
    TraceSnapshotVersion,
    TraceTopologySourceStatus,
)
from app.services.bastion_trace.privacy_policy import TracePrivacyPolicy
from app.services.bastion_trace.proof_packet import TraceProofPacketAssembler
from app.services.bastion_trace.proof_packet_projection import TraceProofPacketApiProjection

NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _graph(snapshot_id: str, relationship_id: str) -> TraceGraphDTO:
    provenance = TraceGraphProvenanceDTO(
        producer="bitcoin-topology-adapter",
        stage="topology",
        evidence=[
            TraceGraphEvidenceReferenceDTO(
                reference=f"observation:{relationship_id}",
                source_name="bitcoin_core_rpc",
                source_type="public_chain",
            )
        ],
        topology_snapshot_id=f"topology:{snapshot_id}",
    )
    metadata = TraceGraphMetadataDTO(
        graph_id="trace_graph:1",
        graph_version="trace-graph-v1",
        snapshot_version=TraceSnapshotVersion.V1,
        api_version=TraceGraphApiVersion.V1,
        schema_version="trace-graph-schema-v1",
        builder_version="trace-graph-builder-v1",
        analysis_version="trace-analysis-v1",
        chain="bitcoin",
        graph_hash="abc",
        created_at=NOW,
        topology_source_status=TraceTopologySourceStatus.AUTHORITATIVE,
        topology_snapshot_id=f"topology:{snapshot_id}",
    )
    return TraceGraphDTO(
        metadata=metadata,
        objects=[
            TraceGraphObjectDTO(id="address:1", kind="address", label="bc1q", provenance=provenance),
            TraceGraphObjectDTO(id="tx:1", kind="transaction", label="tx", provenance=provenance),
        ],
        relationships=[
            TraceGraphRelationshipDTO(
                id=relationship_id,
                source_id="address:1",
                target_id="tx:1",
                relationship_type="address_participates_in_transaction",
                direction="directed",
                originating_observation_id="observation:1",
                provenance=provenance,
            )
        ],
        observations=[],
        snapshot=TraceGraphSnapshotDTO(
            snapshot_id=snapshot_id,
            graph_id="trace_graph:1",
            metadata=metadata,
            object_ids=("address:1", "tx:1"),
            relationship_ids=(relationship_id,),
            observation_ids=("observation:1",),
            report_fact_ids=(),
            topology_snapshot_id=f"topology:{snapshot_id}",
        ),
    )


def test_packet_membership_identity_and_order_are_deterministic() -> None:
    assembler = TraceProofPacketAssembler()
    graph = _graph("snapshot:a", "relationship:a")
    first = assembler.assemble(
        trace_id=1,
        subject="bc1q",
        claim_capture_id="trace_report:1",
        graph=graph,
        claims=(),
        disagreements=(),
        historical=True,
    )
    second = assembler.assemble(
        trace_id=1,
        subject="bc1q",
        claim_capture_id="trace_report:1",
        graph=graph,
        claims=(),
        disagreements=(),
        historical=True,
    )
    assert first.packet_id == second.packet_id
    assert first.packet_digest == second.packet_digest
    assert first.evidence == second.evidence
    assert first.evidence[0].linked_relationship_ids == ("relationship:a",)


def test_historical_packet_a_does_not_receive_b_evidence() -> None:
    assembler = TraceProofPacketAssembler()
    packet_a = assembler.assemble(
        trace_id=1,
        subject="bc1q",
        claim_capture_id="trace_report:1",
        graph=_graph("snapshot:a", "relationship:a"),
        claims=(),
        disagreements=(),
        historical=True,
    )
    packet_b = assembler.assemble(
        trace_id=1,
        subject="bc1q",
        claim_capture_id="trace_report:1",
        graph=_graph("snapshot:b", "relationship:b"),
        claims=(),
        disagreements=(),
        historical=True,
    )
    assert {item.linked_relationship_ids for item in packet_a.evidence} == {
        ("relationship:a",)
    }
    assert {item.linked_relationship_ids for item in packet_b.evidence} == {
        ("relationship:b",)
    }


def test_projection_is_default_deny_and_never_upgrades_verification() -> None:
    packet = TraceProofPacketAssembler().assemble(
        trace_id=1,
        subject="bc1q",
        claim_capture_id="trace_report:1",
        graph=_graph("snapshot:a", "relationship:a"),
        claims=(),
        disagreements=(),
        historical=False,
    )
    dto = TraceProofPacketApiProjection().project(packet)
    assert dto.verification_status.value == "not_verified"
    assert dto.evidence[0].verification_status.value == "not_verified"
    assert "TRACE_EVIDENCE_PRIVACY_CANARY_NEVER_BROWSER" not in dto.model_dump_json()
    assert TracePrivacyPolicy().decision("evidence", "unknown_internal_field").value == "deny"
