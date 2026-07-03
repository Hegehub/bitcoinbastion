"""Pydantic schemas for Access metric catalog and entitlement responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.domain.access.plans import PlanCode


class MetricDefinition(BaseModel):
    name: str = Field(description="Stable metric name.")
    group_code: str = Field(description="Metric group code containing this metric.")
    description: str = Field(default="", description="Human-readable metric description.")
    cost: int | None = Field(default=None, ge=0, description="Base metric credit cost when included.")


class MetricGroup(BaseModel):
    code: str = Field(description="Stable metric group code.")
    name: str = Field(description="Human-facing group name.")
    metrics: list[MetricDefinition] = Field(description="Metrics in this group.")
    scopes: list[str] = Field(description="Scopes associated with this metric group.")
    locked: bool = Field(default=False, description="Whether this group is locked for the current plan.")


class PlanLimits(BaseModel):
    requests_per_minute: int | None = Field(default=None, ge=0)
    requests_per_day: int | None = Field(default=None, ge=0)
    daily_metric_credits: int | None = Field(default=None, ge=0)
    monthly_metric_credits: int | None = Field(default=None, ge=0)
    max_history_days: int | None = Field(default=None, ge=0)
    min_interval: str | None = None
    websocket_streams: int | None = Field(default=None, ge=0)
    child_api_keys: int | str | None = None
    delegated_passes: bool | str | int
    offline_validity_pack: bool | str
    batch_query: bool | None = None


class LockedMetricGroup(BaseModel):
    group_code: str
    required_plan: PlanCode
    reason: str = "upgrade_required"


class MetricCatalogResponse(BaseModel):
    plan: PlanCode
    available_metric_groups: list[str]
    locked_metric_groups: list[LockedMetricGroup]
    limits: PlanLimits
    daily_metric_credits: int | None
    monthly_metric_credits: int | None
    max_history_days: int | None
    min_interval: str | None
    websocket_streams: int | None
    child_api_keys: int | str | None
    delegated_passes: bool | str | int
    offline_validity_pack: bool | str
    batch_query: bool | None = None
    metric_groups: list[MetricGroup] = Field(default_factory=list)


class MetricCostEstimateRequest(BaseModel):
    metrics: list[str] = Field(min_length=1)
    history_days: int | None = Field(default=None, ge=0)
    interval: str | None = None


class MetricCostEstimateResponse(BaseModel):
    metrics: list[str]
    estimated_cost: int = Field(ge=0)
    history_days: int | None = None
    interval: str | None = None


class SubscriptionEntitlementOverlay(BaseModel):
    plan_code: PlanCode
    plan_name: str
    positioning: str
    metric_groups: list[str]
    allowed_scopes: list[str]
    limits: PlanLimits
    issuer_signature: dict[str, Any] | None = None


class SubscriptionEntitlementResponse(BaseModel):
    plan_code: PlanCode
    status: str
    valid_from: Any
    valid_until: Any
    grace_until: Any | None = None
    metric_groups: list[str]
    scopes: list[str]
    limits: dict[str, Any]
    crypto_epoch: int
    issuer_key_id: str | None = None
    created_at: Any


class AccessChallengeCreate(BaseModel):
    certificate_fingerprint: str
    origin: str
    requested_scopes: list[str] = Field(min_length=1)
    device_key_fingerprint: str | None = None


class AccessChallengeResponse(BaseModel):
    challenge_id: str
    challenge_hash: str
    challenge_payload: dict[str, Any]
    expires_at: Any
    status: str


class AccessSessionCreate(BaseModel):
    certificate_fingerprint: str
    challenge_id: str
    origin: str
    device_key_fingerprint: str
    challenge_signature: str
    client_session_public_key: str | None = None
    requested_scopes: list[str] | None = None


class AccessSessionResponse(BaseModel):
    session_token: str
    session_hash_fingerprint: str
    certificate_fingerprint: str
    device_key_fingerprint: str
    plan_code: PlanCode
    scopes: list[str]
    expires_at: Any
    policy_mode: str
    requires_request_signing: bool


__all__ = [
    "AccessChallengeCreate",
    "AccessChallengeResponse",
    "AccessSessionCreate",
    "AccessSessionResponse",
    "LockedMetricGroup",
    "MetricCatalogResponse",
    "MetricCostEstimateRequest",
    "MetricCostEstimateResponse",
    "MetricDefinition",
    "MetricGroup",
    "PlanLimits",
    "SubscriptionEntitlementOverlay",
    "SubscriptionEntitlementResponse",
]
