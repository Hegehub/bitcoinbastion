"""Feature-54 projections for backend-assembled Trace Proof Packets."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from bastion_ui.domain.prompt13 import TraceClaimViewModel
from bastion_ui.transport.generated_schemas import (
    SafeBitcoinNetworkClaimValueDTO,
    SafeRiskBandClaimValueDTO,
    SafeTraceClaimDTO,
    SafeTraceEvidenceDTO,
    SafeTraceProofPacketDTO,
)


class FrozenPacketViewModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class TraceEvidenceViewModel(FrozenPacketViewModel):
    evidence_id: str
    kind: str
    reference: str
    producer: str
    source_category: str
    captured_at: str
    linked_claim_ids: tuple[str, ...]
    linked_relationship_ids: tuple[str, ...]
    integrity_status: str
    verification_status: str
    limitations: tuple[str, ...]


class TracePacketDisagreementViewModel(FrozenPacketViewModel):
    evaluation_id: str
    status: str
    resolution_status: str
    claim_ids: tuple[str, ...]
    limitations: tuple[str, ...]


class TraceProofPacketViewModel(FrozenPacketViewModel):
    packet_id: str
    graph_snapshot_id: str
    subject: str
    captured_at: str
    historical: bool
    claims: tuple[TraceClaimViewModel, ...]
    disagreements: tuple[TracePacketDisagreementViewModel, ...]
    evidence: tuple[TraceEvidenceViewModel, ...]
    packet_digest: str
    integrity_status: str
    verification_status: str
    limitations: tuple[str, ...]


def _value(value: object) -> str:
    return str(getattr(value, "root", value))


def _claim(claim: SafeTraceClaimDTO) -> TraceClaimViewModel:
    if isinstance(claim.value, SafeRiskBandClaimValueDTO):
        kind, label = "risk_band", claim.value.band
    elif isinstance(claim.value, SafeBitcoinNetworkClaimValueDTO):
        kind, label = "bitcoin_network", claim.value.network
    else:  # pragma: no cover - generated strict union rejects this
        raise ValueError("unsupported_trace_claim_value")
    return TraceClaimViewModel(
        id=claim.id,
        subject_id=claim.subject.object_id,
        subject_label=claim.subject.public_value,
        predicate=claim.predicate,
        value_kind=kind,
        value_label=label,
        producer=claim.producer,
        source=claim.source,
        producer_version=claim.producer_version,
        confidence="Not provided" if claim.confidence is None else str(claim.confidence),
        limitations=tuple(claim.limitations),
    )


def _evidence(item: SafeTraceEvidenceDTO) -> TraceEvidenceViewModel:
    return TraceEvidenceViewModel(
        evidence_id=item.evidence_id,
        kind=_value(item.kind),
        reference=item.reference,
        producer=item.producer,
        source_category=item.source_category,
        captured_at=item.captured_at.isoformat(),
        linked_claim_ids=tuple(item.linked_claim_ids or ()),
        linked_relationship_ids=tuple(item.linked_relationship_ids or ()),
        integrity_status=_value(item.integrity_status),
        verification_status=_value(item.verification_status),
        limitations=tuple(item.limitations or ()),
    )


def adapt_trace_proof_packet(packet: SafeTraceProofPacketDTO) -> TraceProofPacketViewModel:
    """Copy only the strict safe contract; never assemble or verify a packet."""
    return TraceProofPacketViewModel(
        packet_id=packet.packet_id,
        graph_snapshot_id=packet.graph_snapshot_id,
        subject=packet.subject,
        captured_at=packet.captured_at.isoformat(),
        historical=packet.historical,
        claims=tuple(_claim(item) for item in packet.claims),
        disagreements=tuple(
            TracePacketDisagreementViewModel(
                evaluation_id=item.evaluation_id,
                status=item.status,
                resolution_status=item.resolution_status,
                claim_ids=tuple(claim.id for claim in item.claims),
                limitations=tuple(item.limitations),
            )
            for item in packet.disagreements
        ),
        evidence=tuple(_evidence(item) for item in packet.evidence),
        packet_digest=packet.packet_digest,
        integrity_status=_value(packet.integrity_status),
        verification_status=_value(packet.verification_status),
        limitations=tuple(packet.limitations or ()),
    )
