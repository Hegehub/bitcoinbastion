from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TraceGraphApiVersion(str, Enum):
    V1 = "trace-graph-api-v1"


class TraceSnapshotVersion(str, Enum):
    V1 = "trace-snapshot-v1"


class TraceGraphErrorCode(str, Enum):
    GRAPH_NOT_FOUND = "GRAPH_NOT_FOUND"
    GRAPH_VALIDATION_FAILED = "GRAPH_VALIDATION_FAILED"


class TraceGraphError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: TraceGraphErrorCode
    message: str


class TraceGraphEvidenceReferenceDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: str
    source_name: str
    source_type: str


class TraceGraphProvenanceDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    producer: str
    stage: str
    observations: list[str] = Field(default_factory=list)
    evidence: list[TraceGraphEvidenceReferenceDTO] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class TraceGraphObjectDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: str
    label: str
    provenance: TraceGraphProvenanceDTO
    limitations: list[str] = Field(default_factory=list)


class TraceGraphRelationshipDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_id: str
    target_id: str
    relationship_type: str
    direction: str
    originating_observation_id: str
    provenance: TraceGraphProvenanceDTO
    confidence: float | None = None
    limitations: list[str] = Field(default_factory=list)


class TraceGraphObservationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: str
    subject: str
    value: str
    provenance: TraceGraphProvenanceDTO
    limitations: list[str] = Field(default_factory=list)


class TraceGraphMetadataDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    graph_version: str
    snapshot_version: TraceSnapshotVersion
    api_version: TraceGraphApiVersion
    schema_version: str
    builder_version: str
    analysis_version: str
    chain: str
    graph_hash: str
    created_at: datetime
    limitations: list[str] = Field(default_factory=list)


class TraceGraphSnapshotDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: str
    graph_id: str
    metadata: TraceGraphMetadataDTO
    object_ids: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    observation_ids: tuple[str, ...]
    report_fact_ids: tuple[str, ...]


class TraceGraphDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: TraceGraphMetadataDTO
    objects: list[TraceGraphObjectDTO]
    relationships: list[TraceGraphRelationshipDTO]
    observations: list[TraceGraphObservationDTO]
    snapshot: TraceGraphSnapshotDTO


class TraceGraphHistoryEntryDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    graph_id: str
    graph_version: str
    snapshot_version: TraceSnapshotVersion
    api_version: TraceGraphApiVersion
    schema_version: str
    builder_version: str
    analysis_version: str
    created_at: datetime
    provenance_summary: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class TraceGraphHistoryDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    entries: list[TraceGraphHistoryEntryDTO]
