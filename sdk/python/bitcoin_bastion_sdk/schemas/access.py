from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AccessChallenge(BaseModel):
    challenge_id: str
    challenge_payload: str
    expires_at: datetime
    requested_scopes: list[str]
    origin: str


class AccessSession(BaseModel):
    session_token: str = Field(repr=False)
    expires_at: datetime
    scopes: list[str]
    plan_code: str
    policy_mode: str | None = None


class AccessMe(BaseModel):
    certificate_fingerprint: str
    plan_code: str
    entitlement_status: str
    active_scopes: list[str]
    session_expiry: datetime


class AccessEntitlement(BaseModel):
    plan_code: str
    allowed_metric_groups: list[str]
    locked_metric_groups: list[dict[str, Any]] = Field(default_factory=list)
    scopes: list[str]
    status: str


class AccessLimits(BaseModel):
    plan_code: str
    limits: dict[str, Any]


class AccessPolicyDecision(BaseModel):
    decision: str
    allowed: bool
    reason_code: str | None = None
