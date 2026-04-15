from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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


class PolicyCheckResponse(BaseModel):
    allowed: bool
    violations: list[str]
    next_actions: list[str]
    evaluated_policy: str
    applied_rules: list[PolicyRuleOut]


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
