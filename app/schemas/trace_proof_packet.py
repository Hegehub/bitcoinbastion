from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.trace_disagreement import SafeTraceClaimDTO, SafeTraceDisagreementDTO


class TraceEvidenceKind(str, Enum):
    TOPOLOGY_RELATIONSHIP_SUPPORT = "topology_relationship_support"
    CLAIM_INPUT_REFERENCE = "claim_input_reference"
    REPORT_EVIDENCE_REFERENCE = "report_evidence_reference"


class TraceEvidenceIntegrityStatus(str, Enum):
    NOT_CHECKED = "not_checked"
    CONTENT_INTEGRITY_CHECKED = "content_integrity_checked"


class TraceEvidenceVerificationStatus(str, Enum):
    NOT_VERIFIED = "not_verified"
    VERIFICATION_UNAVAILABLE = "verification_unavailable"


class SafeTraceEvidenceDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    kind: TraceEvidenceKind
    reference: str
    producer: str
    source_category: str
    captured_at: datetime
    linked_claim_ids: tuple[str, ...] = ()
    linked_relationship_ids: tuple[str, ...] = ()
    integrity_status: TraceEvidenceIntegrityStatus
    verification_status: TraceEvidenceVerificationStatus
    limitations: tuple[str, ...] = ()


class TraceProofPacketTopologyReferenceDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_snapshot_id: str
    topology_snapshot_id: str | None
    node_ids: tuple[str, ...]
    relationship_ids: tuple[str, ...]


class SafeTraceProofPacketDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    packet_id: str
    packet_schema_version: str
    assembler_version: str
    trace_id: int
    graph_snapshot_id: str
    claim_capture_id: str
    subject: str
    captured_at: datetime
    historical: bool
    topology: TraceProofPacketTopologyReferenceDTO
    claims: tuple[SafeTraceClaimDTO, ...]
    disagreements: tuple[SafeTraceDisagreementDTO, ...]
    evidence: tuple[SafeTraceEvidenceDTO, ...]
    packet_digest: str
    integrity_status: TraceEvidenceIntegrityStatus
    verification_status: TraceEvidenceVerificationStatus
    advisory_only: bool = True
    not_legal_verification: bool = True
    not_bitcoin_consensus_proof: bool = True
    limitations: tuple[str, ...] = Field(default_factory=tuple)
