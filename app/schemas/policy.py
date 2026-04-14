from datetime import datetime

from pydantic import BaseModel, Field


class PolicyCheckRequest(BaseModel):
    policy_name: str = Field(min_length=1)
    wallet_health_score: float = Field(ge=0.0, le=100.0)
    transaction_amount_sats: int = Field(gt=0)


class PolicyRuleOut(BaseModel):
    rule_key: str
    rule_value: str
    severity: str


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
