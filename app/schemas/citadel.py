from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CitadelFindingOut(BaseModel):
    title: str
    severity: str
    domain: str
    detail: str


class CitadelFreshnessOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    assessment_generated_at: str | None = None
    cache_source: str | None = None
    cache_age_seconds: int | None = None
    recompute_reason: str | None = None


class CitadelScoreBreakdownOut(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    custody_resilience_score: float = Field(ge=0.0, le=100.0)
    recovery_readiness_score: float = Field(ge=0.0, le=100.0)
    privacy_resilience_score: float = Field(ge=0.0, le=100.0)
    treasury_resilience_score: float = Field(ge=0.0, le=100.0)
    vendor_independence_score: float = Field(ge=0.0, le=100.0)
    inheritance_readiness_score: float = Field(ge=0.0, le=100.0)
    fee_survivability_score: float = Field(ge=0.0, le=100.0)
    policy_maturity_score: float = Field(ge=0.0, le=100.0)
    operational_hygiene_score: float = Field(ge=0.0, le=100.0)


class CitadelAssessmentOut(CitadelScoreBreakdownOut):
    id: int
    owner_type: str
    owner_id: int
    critical_findings: list[CitadelFindingOut] = Field(default_factory=list)
    warnings: list[CitadelFindingOut] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    explainability: dict[str, object] = Field(default_factory=dict)
    freshness: CitadelFreshnessOut = Field(default_factory=CitadelFreshnessOut)
    generated_at: datetime
    created_at: datetime
    updated_at: datetime


class CitadelAssessmentRecalculateIn(BaseModel):
    owner_type: str = Field(default="user", min_length=3, max_length=40)
    owner_id: int = Field(gt=0)


class RecoveryArtifactOut(BaseModel):
    artifact_type: str
    label: str
    is_verified: bool
    required_for_recovery: bool


class RecoveryReadinessOut(BaseModel):
    recovery_readiness_score: float = Field(ge=0.0, le=1.0)
    recoverability_assumption: str
    warnings: list[str] = Field(default_factory=list)
    artifact_summary: dict[str, object] = Field(default_factory=dict)
    human_dependency_score: float = Field(ge=0.0, le=1.0)
    freshness: dict[str, object] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    explainability: dict[str, object] = Field(default_factory=dict)


class CitadelOverviewOut(BaseModel):
    owner_type: str
    owner_id: int
    overall_score: float = Field(ge=0.0, le=100.0)
    recovery_readiness_score: float = Field(ge=0.0, le=1.0)
    top_findings: list[str] = Field(default_factory=list)
    freshness: CitadelFreshnessOut = Field(default_factory=CitadelFreshnessOut)


class CitadelDependencyGraphOut(BaseModel):
    nodes: list[dict[str, object]] = Field(default_factory=list)
    edges: list[dict[str, object]] = Field(default_factory=list)
    single_points_of_failure: list[dict[str, object]] = Field(default_factory=list)
    findings: list[dict[str, object]] = Field(default_factory=list)
    freshness: dict[str, object] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    explainability: dict[str, object] = Field(default_factory=dict)


class CitadelSimulationIn(BaseModel):
    owner_id: int = Field(gt=0)
    scenario_code: str = Field(min_length=3, max_length=80)


class CitadelSimulationOut(BaseModel):
    owner_id: int
    scenario_code: str
    survivability_score: float = Field(ge=0.0, le=1.0)
    blocked_paths: list[str] = Field(default_factory=list)
    remaining_paths: list[str] = Field(default_factory=list)
    critical_failure_points: list[str] = Field(default_factory=list)
    recommended_remediations: list[str] = Field(default_factory=list)
    freshness: dict[str, object] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    explainability: dict[str, object] = Field(default_factory=dict)


class CitadelRepairPlanOut(BaseModel):
    owner_id: int
    items: list[dict[str, object]] = Field(default_factory=list)
    freshness: dict[str, object] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    explainability: dict[str, object] = Field(default_factory=dict)


class CitadelPolicyChecksOut(BaseModel):
    owner_id: int
    policy_maturity_score: float = Field(ge=0.0, le=100.0)
    maturity: str
    gaps: list[str] = Field(default_factory=list)
    freshness: dict[str, object] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    explainability: dict[str, object] = Field(default_factory=dict)


class CitadelInheritanceOut(BaseModel):
    owner_id: int
    status: str
    completeness_score: float = Field(ge=0.0, le=1.0)
    human_dependency_score: float = Field(ge=0.0, le=1.0)
    operational_readability_score: float = Field(ge=0.0, le=1.0)
    critical_gaps: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    freshness: dict[str, object] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    explainability: dict[str, object] = Field(default_factory=dict)
