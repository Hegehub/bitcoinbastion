from __future__ import annotations

from app.schemas.trace_proof_packet import (
    SafeTraceEvidenceDTO,
    SafeTraceProofPacketDTO,
    TraceEvidenceIntegrityStatus,
    TraceEvidenceKind,
    TraceEvidenceVerificationStatus,
    TraceProofPacketTopologyReferenceDTO,
)
from app.services.bastion_trace.disagreement.api_projection import (
    TraceDisagreementApiProjection,
)
from app.services.bastion_trace.privacy_policy import TracePrivacyPolicy
from app.services.bastion_trace.proof_packet import (
    PACKET_ASSEMBLER_VERSION,
    PACKET_SCHEMA_VERSION,
    TracePacketEvidence,
    TraceProofPacket,
)


class TraceProofPacketApiProjection:
    """Central-policy projection of a backend-assembled packet."""

    def __init__(self, policy: TracePrivacyPolicy | None = None) -> None:
        self._policy = policy or TracePrivacyPolicy()
        self._disagreement = TraceDisagreementApiProjection(self._policy)

    def project(self, packet: TraceProofPacket) -> SafeTraceProofPacketDTO:
        values = self._policy.allowlisted(
            "proof_packet",
            {
                "packet_id": packet.packet_id,
                "packet_schema_version": PACKET_SCHEMA_VERSION,
                "assembler_version": PACKET_ASSEMBLER_VERSION,
                "trace_id": packet.trace_id,
                "graph_snapshot_id": packet.graph_snapshot_id,
                "claim_capture_id": packet.claim_capture_id,
                "subject": packet.subject,
                "captured_at": packet.captured_at,
                "historical": packet.historical,
                "topology": TraceProofPacketTopologyReferenceDTO(
                    graph_snapshot_id=packet.graph_snapshot_id,
                    topology_snapshot_id=packet.graph.snapshot.topology_snapshot_id,
                    node_ids=packet.graph.snapshot.object_ids,
                    relationship_ids=packet.graph.snapshot.relationship_ids,
                ),
                "claims": tuple(self._disagreement.claim(item) for item in packet.claims),
                "disagreements": tuple(
                    self._disagreement.evaluation(packet.graph_snapshot_id, item)
                    for item in packet.disagreements
                ),
                "evidence": tuple(self._evidence(item) for item in packet.evidence),
                "packet_digest": packet.packet_digest,
                "integrity_status": TraceEvidenceIntegrityStatus.CONTENT_INTEGRITY_CHECKED,
                "verification_status": TraceEvidenceVerificationStatus.NOT_VERIFIED,
                "advisory_only": True,
                "not_legal_verification": True,
                "not_bitcoin_consensus_proof": True,
                "limitations": packet.limitations,
            },
        )
        return SafeTraceProofPacketDTO.model_validate(values)

    def _evidence(self, item: TracePacketEvidence) -> SafeTraceEvidenceDTO:
        values = self._policy.allowlisted(
            "evidence",
            {
                "evidence_id": item.evidence_id,
                "kind": TraceEvidenceKind(item.kind),
                "reference": item.reference,
                "producer": item.producer,
                "source_category": item.source_category,
                "captured_at": item.captured_at,
                "linked_claim_ids": item.linked_claim_ids,
                "linked_relationship_ids": item.linked_relationship_ids,
                "integrity_status": TraceEvidenceIntegrityStatus.NOT_CHECKED,
                "verification_status": TraceEvidenceVerificationStatus.NOT_VERIFIED,
                "limitations": item.limitations,
            },
        )
        return SafeTraceEvidenceDTO.model_validate(values)
