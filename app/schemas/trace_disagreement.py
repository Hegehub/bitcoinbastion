from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class SafeRiskBandClaimValueDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["risk_band"]
    band: str


class SafeBitcoinNetworkClaimValueDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["bitcoin_network"]
    network: str


SafeTraceClaimValueDTO = Annotated[
    SafeRiskBandClaimValueDTO | SafeBitcoinNetworkClaimValueDTO, Field(discriminator="kind")
]


class SafeTraceClaimSubjectDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    object_id: str
    public_value: str


class SafeTraceClaimProvenanceDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input_references: tuple[str, ...]
    limitations: tuple[str, ...]


class SafeTraceClaimDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    subject: SafeTraceClaimSubjectDTO
    predicate: str
    value: SafeTraceClaimValueDTO
    producer: str
    source: str
    producer_version: str
    evaluated_at: datetime
    confidence: float | None
    provenance: SafeTraceClaimProvenanceDTO
    limitations: tuple[str, ...]


class SafeTraceDisagreementCoverageDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eligible_claim_count: int
    eligible_producer_count: int
    unavailable_producer_count: int
    insufficient_producer_count: int
    failed_producer_count: int


class SafeTraceDisagreementDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evaluation_id: str
    status: str
    resolution_status: str
    subject: SafeTraceClaimSubjectDTO | None
    predicate: str | None
    claims: tuple[SafeTraceClaimDTO, ...]
    coverage: SafeTraceDisagreementCoverageDTO
    evaluator_version: str
    graph_snapshot_id: str
    limitations: tuple[str, ...]


class SafeTraceDisagreementCollectionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    graph_snapshot_id: str
    evaluations: tuple[SafeTraceDisagreementDTO, ...]
