from pydantic import BaseModel, Field


class PolicyCheckRequest(BaseModel):
    policy_name: str = Field(min_length=1)
    wallet_health_score: float = Field(ge=0.0, le=100.0)
    transaction_amount_sats: int = Field(gt=0)


class PolicyCheckResponse(BaseModel):
    allowed: bool
    violations: list[str]
    next_actions: list[str]
