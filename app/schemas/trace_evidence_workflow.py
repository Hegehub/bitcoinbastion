from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.schemas.trace_proof_packet import SafeTraceEvidenceDTO


class EvidenceLineageNodeKind(str, Enum):
    SOURCE_REFERENCE = "source_reference"
    EVIDENCE = "evidence"
    TOPOLOGY_RELATIONSHIP = "topology_relationship"
    CLAIM = "claim"
    GRAPH_SNAPSHOT = "graph_snapshot"
    REPORT_CAPTURE = "report_capture"
    PROOF_PACKET = "proof_packet"


class EvidenceLineageRelation(str, Enum):
    PRODUCED_FROM = "produced_from"
    SUPPORTS = "supports"
    CAPTURED_IN = "captured_in"
    INCLUDED_IN = "included_in"
    REFERENCED_BY = "referenced_by"


class EvidenceLineageCompleteness(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    TRUNCATED = "truncated"
    UNAVAILABLE = "unavailable"


class EvidenceReplayEligibility(str, Enum):
    REPLAYABLE = "replayable"
    NOT_REPLAYABLE = "not_replayable"
    INPUT_UNAVAILABLE = "input_unavailable"
    VERSION_UNAVAILABLE = "version_unavailable"
    UNSUPPORTED_LEGACY = "unsupported_legacy"


class EvidenceReplayStatus(str, Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    NOT_REPLAYABLE = "not_replayable"
    INPUT_UNAVAILABLE = "input_unavailable"
    VERSION_UNAVAILABLE = "version_unavailable"
    EXECUTION_FAILED = "execution_failed"


class EvidenceVerificationScope(str, Enum):
    EVIDENCE_IDENTITY_INTEGRITY = "evidence_identity_integrity"


class EvidenceVerificationStatus(str, Enum):
    VERIFIED = "verified"
    FAILED = "failed"
    NOT_RUN = "not_run"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"


class EvidenceLineageNodeDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: EvidenceLineageNodeKind
    label: str
    producer: str | None = None
    producer_version: str | None = None
    captured_at: datetime | None = None
    limitations: tuple[str, ...] = ()


class EvidenceLineageEdgeDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_id: str
    target_id: str
    relation: EvidenceLineageRelation
    direction: str = "directed"


class EvidenceLineagePathDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path_id: str
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]


class SafeEvidenceLineageDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence: SafeTraceEvidenceDTO
    graph_snapshot_id: str
    proof_packet_id: str
    historical: bool
    completeness: EvidenceLineageCompleteness
    nodes: tuple[EvidenceLineageNodeDTO, ...]
    edges: tuple[EvidenceLineageEdgeDTO, ...]
    paths: tuple[EvidenceLineagePathDTO, ...]
    limitations: tuple[str, ...] = ()


class SafeEvidenceReplayDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    replay_id: str
    evidence_id: str
    graph_snapshot_id: str
    eligibility: EvidenceReplayEligibility
    status: EvidenceReplayStatus
    immutable_input_ids: tuple[str, ...]
    method_id: str
    method_version: str
    original_identity: str
    reproduced_identity: str | None
    comparison_scope: str
    replayed_at: datetime
    limitations: tuple[str, ...] = ()


class SafeEvidenceVerificationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verification_id: str
    evidence_id: str
    graph_snapshot_id: str
    verifier_id: str
    verifier_version: str
    scope: EvidenceVerificationScope
    status: EvidenceVerificationStatus
    verified_at: datetime
    proposition: str
    limitations: tuple[str, ...] = ()


class SafeEvidenceExportDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    export_id: str
    evidence_id: str
    graph_snapshot_id: str
    proof_packet_id: str
    schema_version: str
    media_type: str
    filename: str
    content: str
    content_digest: str
    integrity_status: str
    limitations: tuple[str, ...] = ()
