"""Policy decision objects for the Access domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.access.plans import PlanCode


class PolicyDecision(StrEnum):
    """Explicit policy outcomes for protected Access requests."""

    ALLOW = "allow"
    DENY = "deny"
    UPGRADE_REQUIRED = "upgrade_required"
    STEP_UP_REQUIRED = "step_up_required"
    QUOTA_EXCEEDED = "quota_exceeded"
    METRIC_NOT_ALLOWED = "metric_not_allowed"
    REVOKED = "revoked"
    EXPIRED = "expired"
    RECOVERY_REQUIRED = "recovery_required"
    ONLINE_CHECK_REQUIRED = "online_check_required"
    READ_ONLY = "read_only"
    LOCKDOWN_REQUIRED = "lockdown_required"
    INVALID_SIGNATURE = "invalid_signature"
    INVALID_SESSION = "invalid_session"
    INSUFFICIENT_SCOPE = "insufficient_scope"
    OBJECT_ACCESS_DENIED = "object_access_denied"


@dataclass(frozen=True, slots=True)
class AccessDecision:
    """Pydantic-free Access domain decision object."""

    decision: PolicyDecision
    reason: str
    required_plan: PlanCode | None = None
    current_plan: PlanCode | None = None
    requested_scope: str | None = None
    requested_metric_group: str | None = None
    upgrade_available: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
