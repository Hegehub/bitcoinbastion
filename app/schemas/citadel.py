from datetime import datetime

from pydantic import BaseModel, Field


class CitadelFindingOut(BaseModel):
    title: str
    severity: str
    domain: str
    detail: str


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
    freshness: dict[str, object] = Field(default_factory=dict)
    generated_at: datetime
    created_at: datetime
    updated_at: datetime


class CitadelAssessmentRecalculateIn(BaseModel):
    owner_type: str = Field(default="user", min_length=3, max_length=40)
    owner_id: int = Field(gt=0)
