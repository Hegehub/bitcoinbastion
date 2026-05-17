from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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


class MiningPoolRegistryMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    pool_name: str
    website_url: str | None = None
    operator_name: str | None = None
    country: str | None = None
    jurisdiction: str | None = None
    public_documentation_url: str | None = None
    notes: str | None = None
    source_quality: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    freshness: int | None = Field(default=None, ge=0)


class MiningPoolEndpointCreate(BaseModel):
    endpoint_type: str = "api"
    endpoint_url: str
    network: str = "unknown"
    source_type: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    is_verified: bool = False
    freshness: int | None = Field(default=None, ge=0)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


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


class StratumV2CapabilityEvaluationInput(BaseModel):
    supports_stratum_v2: str = "unknown"
    supports_job_declaration: str = "unknown"
    supports_template_distribution: str = "unknown"
    supports_template_provider: str = "unknown"
    supports_translator_proxy: str = "unknown"
    supports_encrypted_channel: str = "unknown"
    miner_can_build_templates: str = "unknown"
    pool_can_override_templates: str = "unknown"
    miner_template_control_level: str = "unknown"
    source_type: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    freshness_seconds: int | None = Field(default=None, ge=0)
    is_fallback: bool = False
    is_synthetic: bool = False
    is_verified: bool = False


class StratumV2CapabilityEvaluationOut(BaseModel):
    capability_summary: str
    missing_capabilities: list[str] = Field(default_factory=list)
    positive_factors: list[str] = Field(default_factory=list)
    negative_factors: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    explainability: MiningExplainabilityOut = Field(default_factory=MiningExplainabilityOut)
    statuses: dict[str, str] = Field(default_factory=dict)


class StratumV2AdoptionSummaryOut(BaseModel):
    total_pools: int = 0
    sv2_supported_count: int = 0
    job_declaration_supported_count: int = 0
    template_control_supported_count: int = 0
    unknown_count: int = 0
    claimed_unverified_count: int = 0
    adoption_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
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
