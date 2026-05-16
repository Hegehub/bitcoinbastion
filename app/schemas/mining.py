from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MiningFreshnessOut(BaseModel):
    observed_at: datetime | None = None
    age_seconds: int | None = None
    freshness_band: str = "unknown"


class MiningExplainabilityOut(BaseModel):
    drivers: list[str] = Field(default_factory=list)
    factor_breakdown: list[dict[str, Any]] = Field(default_factory=list)
    source_quality_impact: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class MiningSourceQualityOut(BaseModel):
    source_type: str = "unknown"
    provider_name: str = "unknown"
    is_verified: bool = False
    is_fallback: bool = False
    is_synthetic: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    freshness: MiningFreshnessOut = Field(default_factory=MiningFreshnessOut)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class MiningPoolCreate(BaseModel):
    pool_key: str
    display_name: str
    provider_name: str = "unknown"


class MiningPoolEndpointOut(BaseModel):
    id: int
    endpoint_type: str
    endpoint_url: str
    network: str
    source_type: str = "unknown"
    provider_name: str = "unknown"
    is_verified: bool = False
    is_fallback: bool = False
    is_synthetic: bool = False
    freshness: MiningFreshnessOut = Field(default_factory=MiningFreshnessOut)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    explainability: MiningExplainabilityOut = Field(default_factory=MiningExplainabilityOut)


class StratumV2CapabilityOut(BaseModel):
    id: int
    capability_state: str = "unknown"
    job_declaration_state: str = "unknown"
    translator_proxy_state: str = "unknown"
    encrypted_channel_state: str = "unknown"
    source_type: str = "unknown"
    provider_name: str = "unknown"
    is_verified: bool = False
    is_fallback: bool = False
    is_synthetic: bool = False
    freshness: MiningFreshnessOut = Field(default_factory=MiningFreshnessOut)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    explainability: MiningExplainabilityOut = Field(default_factory=MiningExplainabilityOut)


class PoolSovereigntyScoreOut(BaseModel):
    id: int
    score_100: float = Field(default=0.0, ge=0.0, le=100.0)
    severity: str = "unknown"
    source_type: str = "unknown"
    provider_name: str = "unknown"
    is_verified: bool = False
    is_fallback: bool = False
    is_synthetic: bool = False
    freshness: MiningFreshnessOut = Field(default_factory=MiningFreshnessOut)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    explainability: MiningExplainabilityOut = Field(default_factory=MiningExplainabilityOut)


class MiningCensorshipRiskOut(BaseModel):
    id: int
    risk_score_100: float = Field(default=0.0, ge=0.0, le=100.0)
    risk_level: str = "unknown"
    source_type: str = "unknown"
    provider_name: str = "unknown"
    is_verified: bool = False
    is_fallback: bool = False
    is_synthetic: bool = False
    freshness: MiningFreshnessOut = Field(default_factory=MiningFreshnessOut)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    explainability: MiningExplainabilityOut = Field(default_factory=MiningExplainabilityOut)


class TemplateControlAssessmentOut(BaseModel):
    id: int
    template_control_state: str = "unknown"
    template_control_owner: str = "unknown"
    template_sovereignty_score_100: float = Field(default=0.0, ge=0.0, le=100.0)
    template_interference_risk_score_100: float = Field(default=0.0, ge=0.0, le=100.0)
    mitm_risk_level: str = "unknown"
    source_type: str = "unknown"
    provider_name: str = "unknown"
    is_verified: bool = False
    is_fallback: bool = False
    is_synthetic: bool = False
    freshness: MiningFreshnessOut = Field(default_factory=MiningFreshnessOut)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    explainability: MiningExplainabilityOut = Field(default_factory=MiningExplainabilityOut)


class MiningSignalOut(BaseModel):
    id: int
    signal_type: str
    severity: str = "unknown"
    title: str = ""
    summary: str = ""
    source_type: str = "unknown"
    provider_name: str = "unknown"
    is_verified: bool = False
    is_fallback: bool = False
    is_synthetic: bool = False
    freshness: MiningFreshnessOut = Field(default_factory=MiningFreshnessOut)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    explainability: MiningExplainabilityOut = Field(default_factory=MiningExplainabilityOut)


class MiningPoolOut(BaseModel):
    id: int
    pool_key: str
    display_name: str
    source_type: str = "unknown"
    provider_name: str = "unknown"
    is_verified: bool = False
    is_fallback: bool = False
    is_synthetic: bool = False
    freshness: MiningFreshnessOut = Field(default_factory=MiningFreshnessOut)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    explainability: MiningExplainabilityOut = Field(default_factory=MiningExplainabilityOut)

    endpoints: list[MiningPoolEndpointOut] = Field(default_factory=list)
    latest_stratum_v2_capability: StratumV2CapabilityOut | None = None
    latest_sovereignty_score: PoolSovereigntyScoreOut | None = None
    latest_censorship_risk: MiningCensorshipRiskOut | None = None
    latest_template_control: TemplateControlAssessmentOut | None = None
    latest_signal: MiningSignalOut | None = None
