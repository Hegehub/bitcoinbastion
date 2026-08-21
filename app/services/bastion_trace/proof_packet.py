from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

from app.schemas.trace_graph import TraceGraphDTO
from app.services.bastion_trace.claims.domain import TraceClaim
from app.services.bastion_trace.disagreement.domain import TraceDisagreementEvaluation

PACKET_SCHEMA_VERSION = "trace-proof-packet-v1"
PACKET_ASSEMBLER_VERSION = "trace-proof-packet-assembler-v1"


@dataclass(frozen=True, slots=True)
class TracePacketEvidence:
    evidence_id: str
    kind: str
    reference: str
    producer: str
    source_category: str
    captured_at: datetime
    linked_claim_ids: tuple[str, ...] = ()
    linked_relationship_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TraceProofPacket:
    packet_id: str
    trace_id: int
    graph_snapshot_id: str
    claim_capture_id: str
    subject: str
    captured_at: datetime
    historical: bool
    graph: TraceGraphDTO
    claims: tuple[TraceClaim, ...]
    disagreements: tuple[TraceDisagreementEvaluation, ...]
    evidence: tuple[TracePacketEvidence, ...]
    packet_digest: str
    limitations: tuple[str, ...]


class TraceProofPacketAssembler:
    """Deterministically packages existing authority; it performs no analysis."""

    def assemble(
        self,
        *,
        trace_id: int,
        subject: str,
        claim_capture_id: str,
        graph: TraceGraphDTO,
        claims: tuple[TraceClaim, ...],
        disagreements: tuple[TraceDisagreementEvaluation, ...],
        historical: bool,
    ) -> TraceProofPacket:
        evidence = self._select_evidence(graph, claims)
        semantic = {
            "schema": PACKET_SCHEMA_VERSION,
            "assembler": PACKET_ASSEMBLER_VERSION,
            "trace_id": trace_id,
            "snapshot_id": graph.snapshot.snapshot_id,
            "claim_capture_id": claim_capture_id,
            "claim_ids": sorted(claim.id for claim in claims),
            "evaluation_ids": sorted(item.id for item in disagreements),
            "evidence_ids": sorted(item.evidence_id for item in evidence),
        }
        canonical = json.dumps(semantic, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        packet_id = f"trace_proof_packet:{digest[:24]}"
        return TraceProofPacket(
            packet_id=packet_id,
            trace_id=trace_id,
            graph_snapshot_id=graph.snapshot.snapshot_id,
            claim_capture_id=claim_capture_id,
            subject=subject,
            captured_at=graph.metadata.created_at,
            historical=historical,
            graph=graph,
            claims=tuple(sorted(claims, key=lambda item: item.id)),
            disagreements=tuple(sorted(disagreements, key=lambda item: item.id)),
            evidence=evidence,
            packet_digest=digest,
            limitations=(
                "Evidence linkage does not mean independent verification.",
                "Packet integrity protects packet membership, not analytical truth.",
                "This packet is advisory and is not legal or Bitcoin consensus proof.",
            ),
        )

    def _select_evidence(
        self, graph: TraceGraphDTO, claims: tuple[TraceClaim, ...]
    ) -> tuple[TracePacketEvidence, ...]:
        selected: dict[str, TracePacketEvidence] = {}
        for relationship in graph.relationships:
            for item in relationship.provenance.evidence:
                evidence_id = _stable_evidence_id(
                    "topology_relationship_support", item.reference, relationship.id
                )
                selected[evidence_id] = TracePacketEvidence(
                    evidence_id=evidence_id,
                    kind="topology_relationship_support",
                    reference=item.reference,
                    producer=relationship.provenance.producer,
                    source_category=item.source_type,
                    captured_at=graph.metadata.created_at,
                    linked_relationship_ids=(relationship.id,),
                    limitations=tuple(relationship.limitations or ()),
                )
        for claim in claims:
            for reference in claim.provenance.input_references:
                evidence_id = _stable_evidence_id("claim_input_reference", reference, claim.id)
                selected[evidence_id] = TracePacketEvidence(
                    evidence_id=evidence_id,
                    kind="claim_input_reference",
                    reference=reference,
                    producer=claim.producer_id,
                    source_category=claim.source_id,
                    captured_at=claim.evaluated_at,
                    linked_claim_ids=(claim.id,),
                    limitations=claim.limitations,
                )
        return tuple(selected[key] for key in sorted(selected))


def stable_evidence_id(kind: str, reference: str, owner_id: str) -> str:
    digest = hashlib.sha256("\x1f".join((kind, reference, owner_id)).encode()).hexdigest()[:24]
    return f"trace_evidence:{digest}"


_stable_evidence_id = stable_evidence_id
