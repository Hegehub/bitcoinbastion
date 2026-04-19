from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ExplainabilityOut, FreshnessOut


class PolicyCheckRequest(BaseModel):
    policy_name: str = Field(min_length=1)
    wallet_health_score: float = Field(ge=0.0, le=100.0)
    transaction_amount_sats: int = Field(gt=0)
    required_approvals: int = Field(default=1, ge=1)


class PolicyRuleOut(BaseModel):
    rule_key: str
    rule_value: str
    severity: str


class PolicyRuleUpsertIn(BaseModel):
    rule_key: Literal["min_wallet_health_score", "max_single_tx_sats", "min_required_approvals"]
    comparator: Literal["gte", "lte", "eq"]
    threshold: int = Field(ge=0)
    severity: Literal["warning", "error"] = "error"


class PolicyCatalogUpsertIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    min_wallet_health_score: int = Field(ge=0, le=100)
    max_single_tx_sats: int = Field(gt=0)
    rules: list[PolicyRuleUpsertIn] = []
    change_justification: str | None = Field(default=None, max_length=2000)


class PolicyCheckResponse(BaseModel):
    allowed: bool
    violations: list[str]
    next_actions: list[str]
    evaluated_policy: str
    applied_rules: list[PolicyRuleOut]
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explainability: ExplainabilityOut = Field(default_factory=ExplainabilityOut)
    data_sources: list[str] = Field(default_factory=list)
    freshness: FreshnessOut = Field(default_factory=FreshnessOut)


class PolicyCatalogOut(BaseModel):
    name: str
    min_wallet_health_score: int
    max_single_tx_sats: int


class PolicyExecutionLogOut(BaseModel):
    id: int
    policy_name: str
    wallet_health_score: int
    transaction_amount_sats: int
    allowed: bool
    violations: list[str]
    next_actions: list[str]
    executed_at: datetime


class PolicyExecutionPolicyBreakdownOut(BaseModel):
    policy_name: str
    total: int
    allowed: int
    blocked: int


class PolicyExecutionSummaryOut(BaseModel):
    total: int
    allowed: int
    blocked: int
    allow_rate: float = Field(ge=0.0, le=1.0)
    by_policy: list[PolicyExecutionPolicyBreakdownOut]


class PolicySimulationRequest(BaseModel):
    baseline_policy_name: str = Field(min_length=1)
    candidate_policy_name: str = Field(min_length=1)
    wallet_health_score: float = Field(ge=0.0, le=100.0)
    transaction_amount_sats: int = Field(gt=0)
    required_approvals: int = Field(default=1, ge=1)


class PolicySimulationDiffOut(BaseModel):
    baseline_allowed: bool
    candidate_allowed: bool
    changed: bool
    added_violations: list[str]
    removed_violations: list[str]
    changed_rules: list[str]
    risk_level: Literal["low", "medium", "high"]
    required_approvals_suggested: int
    governance_actions: list[str]


class PolicySimulationOut(BaseModel):
    baseline: PolicyCheckResponse
    candidate: PolicyCheckResponse
    diff: PolicySimulationDiffOut
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explainability: ExplainabilityOut = Field(default_factory=ExplainabilityOut)
    data_sources: list[str] = Field(default_factory=list)
    freshness: FreshnessOut = Field(default_factory=FreshnessOut)


class PolicyCatalogCompareRequest(BaseModel):
    baseline_policy_name: str = Field(min_length=1)
    candidate_policy_name: str = Field(min_length=1)


class PolicyCatalogCompareOut(BaseModel):
    baseline_policy_name: str
    candidate_policy_name: str
    changed_thresholds: list[str]
    changed_rules: list[str]
    risk_level: Literal["low", "medium", "high"]
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explainability: ExplainabilityOut = Field(default_factory=ExplainabilityOut)
    data_sources: list[str] = Field(default_factory=list)
    freshness: FreshnessOut = Field(default_factory=FreshnessOut)
