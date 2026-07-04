"""Typed context and decision objects for Bastion Access Policy Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.access.plans import PlanCode


@dataclass(frozen=True, slots=True)
class AccessPolicyContext:
    certificate_fingerprint: str | None = None
    pass_lookup_hash: str | None = None
    plan_code: PlanCode | str | None = None
    effective_scopes: set[str] = field(default_factory=set)
    requested_scope: str | None = None
    requested_metric_group: str | None = None
    requested_metric_name: str | None = None
    requested_interval: str | None = None
    requested_history_days: int | None = None
    requested_object_type: str | None = None
    requested_object_id_hash: str | None = None
    request_risk_level: str = "low"
    session_id_hash: str | None = None
    session_status: str = "active"
    session_expires_at: datetime | None = None
    device_id: str | int | None = None
    device_status: str = "active"
    device_risk_score: int | None = None
    entitlement_status: str = "active"
    entitlement_valid_until: datetime | None = None
    entitlement_limits: dict[str, Any] = field(default_factory=dict)
    metric_entitlements: dict[str, Any] = field(default_factory=dict)
    quota_state: dict[str, Any] = field(default_factory=dict)
    revocation_state: dict[str, Any] = field(default_factory=dict)
    offline_mode: bool = False
    business_role: str | None = None
    workspace_id_hash: str | None = None
    is_critical_action: bool = False
    step_up_present: bool = False
    human_intent_verified: bool = False
    legacy_auth_context: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AccessPolicyDecision:
    decision: str
    allowed: bool
    reason_code: str
    human_reason: str
    current_plan: PlanCode | None = None
    required_plan: PlanCode | None = None
    requested_scope: str | None = None
    requested_metric_group: str | None = None
    upgrade_available: bool = False
    step_up_required: bool = False
    quota_remaining: int | None = None
    retry_after_seconds: int | None = None
    audit_required: bool = False
    lockdown_recommended: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
