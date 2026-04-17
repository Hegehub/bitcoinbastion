import json
from datetime import datetime

from pydantic import BaseModel, Field


class TreasuryRequestIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    amount_sats: int = Field(gt=0)
    destination_reference: str = Field(min_length=5, max_length=255)
    policy_name: str = Field(default="default", min_length=1, max_length=120)
    wallet_health_score: float = Field(default=100.0, ge=0.0, le=100.0)


class TreasuryApprovalActionIn(BaseModel):
    policy_name: str = Field(default="default", min_length=1, max_length=120)
    wallet_health_score: float = Field(default=100.0, ge=0.0, le=100.0)
    note: str = Field(default="", max_length=1000)




class TreasuryRejectActionIn(BaseModel):
    note: str = Field(default="", max_length=1000)


class TreasuryRejectOut(BaseModel):
    request_id: int
    status: str
    note: str

class TreasuryApprovalOut(BaseModel):
    request_id: int
    status: str
    approved_count: int
    required_approvals: int
    allowed_by_policy: bool
    violations: list[str]


class TreasuryRequestOut(BaseModel):
    id: int
    title: str
    amount_sats: int
    status: str
    created_at: datetime
    policy_allowed: bool | None = None
    policy_violations: list[str] = []
    approved_count: int = 0
    required_approvals: int = 1

    model_config = {"from_attributes": True}

    @classmethod
    def from_model_with_policy(cls, obj: object) -> "TreasuryRequestOut":
        parsed = cls.model_validate(obj)
        policy_snapshot_json = getattr(obj, "policy_snapshot_json", "{}")
        approved_by_json = getattr(obj, "approved_by_json", "[]")

        snapshot: dict[str, object] = {}
        if isinstance(policy_snapshot_json, str):
            try:
                snapshot = json.loads(policy_snapshot_json)
            except json.JSONDecodeError:
                snapshot = {}

        allowed_flag = snapshot.get("allowed")
        parsed.policy_allowed = allowed_flag if isinstance(allowed_flag, bool) else None
        raw_violations = snapshot.get("violations", [])
        parsed.policy_violations = [str(item) for item in raw_violations] if isinstance(raw_violations, list) else []

        if isinstance(approved_by_json, str):
            try:
                approved = json.loads(approved_by_json)
                parsed.approved_count = len(approved) if isinstance(approved, list) else 0
            except json.JSONDecodeError:
                parsed.approved_count = 0

        parsed.required_approvals = int(getattr(obj, "required_approvals", 1) or 1)
        return parsed
