from datetime import datetime
from pydantic import BaseModel, Field


class ProviderHealthOut(BaseModel):
    provider: str
    provider_name: str = "unknown"
    healthy: bool
    details: str
    confidence: float = 0.0
    freshness_seconds: int = 0
    stale_evidence: bool = False
    is_fallback: bool = False
    is_mock: bool = False
    degradation_reason: str | None = None
    operator_guidance: list[str] = Field(default_factory=list)


class ProviderHealthEvidenceOut(BaseModel):
    provider_name: str
    provider_type: str
    checked_at: datetime
    healthy: bool
    latency_ms: int
    error_type: str | None = None
    error_message: str | None = None
    source_type: str = "unknown"
    is_fallback: bool = False
    is_mock: bool = False
    confidence: float = 0.0
    freshness_seconds: int = 0
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class DeliveryStatsOut(BaseModel):
    sent_24h: int
    failed_24h: int


class JobStatsOut(BaseModel):
    started_24h: int
    failed_24h: int


class ChainStateOut(BaseModel):
    tip_height: int
    observed_block_height: int
    headers_height: int
    confirmation_depth: int
    reorg_risk_score: float
    finality_score: float
    finality_band: str


class RecoverySLOOut(BaseModel):
    status: str
    target: dict[str, object] = Field(default_factory=dict)
    actual: dict[str, object] = Field(default_factory=dict)
    signals: dict[str, object] = Field(default_factory=dict)
    explainability: dict[str, object] = Field(default_factory=dict)


class RuntimeSeverityOut(BaseModel):
    level: str
    escalation_required: bool
    score: int
    dimensions: dict[str, str] = Field(default_factory=dict)
    escalation_conditions: list[str] = Field(default_factory=list)
    operator_guidance: list[str] = Field(default_factory=list)
    explainability: dict[str, object] = Field(default_factory=dict)


class RuntimeDegradedModeOut(BaseModel):
    active: bool
    reasons: list[str] = Field(default_factory=list)
    component_states: dict[str, str] = Field(default_factory=dict)
    confidence_penalty: float = 0.0
    explainability: dict[str, object] = Field(default_factory=dict)




class OperationalEvidencePacketOut(BaseModel):
    packet_type: str
    runtime_state: str
    degraded_dependencies: list[str] = Field(default_factory=list)
    provider_quality: dict[str, object] = Field(default_factory=dict)
    unresolved_critical_findings: int = 0
    delivery_health: dict[str, object] = Field(default_factory=dict)
    drill_status: dict[str, object] = Field(default_factory=dict)
    recovery_slo_status: str = "unknown"
    confidence: float = 0.0
    evidence_refs: list[str] = Field(default_factory=list)
    explainability: dict[str, object] = Field(default_factory=dict)


class OperationsSnapshotOut(BaseModel):
    queue_depth: int
    stale_jobs: int
    providers: list[ProviderHealthOut]
    jobs: JobStatsOut
    deliveries: DeliveryStatsOut
    chain_state: ChainStateOut
    recovery_slo: RecoverySLOOut
    runtime_severity: RuntimeSeverityOut
    degraded_mode: RuntimeDegradedModeOut
    operational_evidence: OperationalEvidencePacketOut
