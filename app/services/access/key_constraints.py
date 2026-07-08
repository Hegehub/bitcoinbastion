"""Constraint validators for Child API Keys and Delegated Passes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.domain.access.plans import PlanCode, normalize_plan_code, plan_rank
from app.domain.access.scopes import ACCESS_SCOPES, FORBIDDEN_SCOPES

_CHILD_KEY_LIMITS: dict[PlanCode, int] = {
    PlanCode.LITE: 0,
    PlanCode.BASIC: 1,
    PlanCode.PLUS: 3,
    PlanCode.PRO: 10,
    PlanCode.BUSINESS: 100,
    PlanCode.ENTERPRISE: 1000,
}
_DELEGATED_PASS_LIMITS: dict[PlanCode, int] = {
    PlanCode.LITE: 0,
    PlanCode.BASIC: 0,
    PlanCode.PLUS: 3,
    PlanCode.PRO: 25,
    PlanCode.BUSINESS: 100,
    PlanCode.ENTERPRISE: 1000,
}
_HIGH_RISK_SCOPE_PREFIXES = ("treasury:", "payregister:admin", "enterprise:", "recovery:")


class KeyConstraintError(ValueError):
    pass


@dataclass(frozen=True)
class ParentAccessContext:
    pass_lookup_hash: str
    certificate_fingerprint: str | None
    plan_code: PlanCode
    effective_scopes: frozenset[str]
    metric_entitlements: frozenset[str]
    entitlement_expires_at: datetime
    session_hash: str | None = None
    device_key_fingerprint: str | None = None
    denied_scopes: frozenset[str] = frozenset()
    can_delegate: bool = False
    risk_level: str = "low"


def validate_scope_subset(parent_scopes: set[str] | frozenset[str], child_scopes: list[str]) -> None:
    normalized = set(child_scopes)
    unsafe = normalized & FORBIDDEN_SCOPES
    if unsafe:
        raise KeyConstraintError("unsafe_scope")
    unknown = normalized - ACCESS_SCOPES
    if unknown:
        raise KeyConstraintError("unknown_scope")
    if not normalized.issubset(set(parent_scopes)):
        raise KeyConstraintError("child_scope_exceeds_parent")


def validate_metric_subset(parent_metrics: set[str] | frozenset[str], child_metrics: list[str] | dict[str, Any] | None) -> None:
    requested = _metric_set(child_metrics)
    if not requested:
        return
    if not requested.issubset(set(parent_metrics)):
        raise KeyConstraintError("child_metric_exceeds_parent")


def validate_expiry_bound(parent_expiry: datetime, child_expiry: datetime) -> None:
    parent = _aware(parent_expiry)
    child = _aware(child_expiry)
    if child > parent:
        raise KeyConstraintError("child_expiry_exceeds_parent")
    if child <= datetime.now(UTC):
        raise KeyConstraintError("child_expiry_invalid")


def validate_plan_child_key_limit(plan_code: PlanCode | str, existing_count: int) -> None:
    plan = normalize_plan_code(plan_code)
    if existing_count >= _CHILD_KEY_LIMITS[plan]:
        raise KeyConstraintError("child_key_limit_exceeded")


def validate_plan_delegated_pass_limit(plan_code: PlanCode | str, existing_count: int) -> None:
    plan = normalize_plan_code(plan_code)
    if existing_count >= _DELEGATED_PASS_LIMITS[plan]:
        raise KeyConstraintError("delegated_pass_limit_exceeded")


def validate_child_key_constraints(parent_context: ParentAccessContext, request: Any, existing_count: int = 0) -> None:
    scopes = list(getattr(request, "scopes", []) or [])
    validate_plan_child_key_limit(parent_context.plan_code, existing_count)
    validate_scope_subset(parent_context.effective_scopes, scopes)
    denied_scopes = set(getattr(request, "denied_scopes", []) or []) | set(parent_context.denied_scopes)
    if set(scopes) & denied_scopes:
        raise KeyConstraintError("child_scope_denied")
    validate_metric_subset(parent_context.metric_entitlements, getattr(request, "metric_entitlements", None))
    validate_expiry_bound(parent_context.entitlement_expires_at, getattr(request, "expires_at"))
    _validate_plan_scope(parent_context.plan_code, scopes)
    if getattr(request, "can_delegate", False) and not parent_context.can_delegate:
        raise KeyConstraintError("child_delegation_not_allowed")
    if _requires_human_intent(parent_context.plan_code, scopes) and not getattr(request, "human_intent_verified", False):
        raise KeyConstraintError("human_intent_required")


def validate_delegated_pass_constraints(parent_context: ParentAccessContext, request: Any, existing_count: int = 0) -> None:
    scopes = list(getattr(request, "scopes", []) or [])
    validate_plan_delegated_pass_limit(parent_context.plan_code, existing_count)
    validate_scope_subset(parent_context.effective_scopes, scopes)
    denied_scopes = set(getattr(request, "denied_scopes", []) or []) | set(parent_context.denied_scopes)
    if set(scopes) & denied_scopes:
        raise KeyConstraintError("delegated_pass_scope_denied")
    validate_metric_subset(parent_context.metric_entitlements, getattr(request, "metric_entitlements", None))
    validate_expiry_bound(parent_context.entitlement_expires_at, getattr(request, "expires_at"))
    _validate_plan_scope(parent_context.plan_code, scopes)
    if (getattr(request, "can_delegate", False) or getattr(request, "can_create_child_keys", False)) and not parent_context.can_delegate:
        raise KeyConstraintError("delegation_not_allowed")


def compute_effective_child_policy(parent_context: ParentAccessContext, requested_constraints: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_code": parent_context.plan_code.value,
        "max_expires_at": parent_context.entitlement_expires_at.isoformat(),
        "allowed_scopes": sorted(parent_context.effective_scopes),
        "allowed_metric_entitlements": sorted(parent_context.metric_entitlements),
        "requested_constraints": requested_constraints,
    }


def child_key_limit(plan_code: PlanCode | str) -> int:
    return _CHILD_KEY_LIMITS[normalize_plan_code(plan_code)]


def delegated_pass_limit(plan_code: PlanCode | str) -> int:
    return _DELEGATED_PASS_LIMITS[normalize_plan_code(plan_code)]


def _metric_set(value: list[str] | dict[str, Any] | None) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, dict):
        groups = value.get("groups", [])
        return {str(item) for item in groups}
    return {str(item) for item in value}


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _validate_plan_scope(plan_code: PlanCode, scopes: list[str]) -> None:
    plan = normalize_plan_code(plan_code)
    if plan == PlanCode.BASIC and any(not scope.endswith(":read") for scope in scopes):
        raise KeyConstraintError("basic_child_key_read_only")
    if plan_rank(plan) < plan_rank(PlanCode.PRO) and any(scope.startswith("treasury:") for scope in scopes):
        raise KeyConstraintError("child_scope_requires_higher_plan")
    if plan_rank(plan) < plan_rank(PlanCode.BUSINESS) and any(scope.startswith("payregister:") for scope in scopes):
        raise KeyConstraintError("child_scope_requires_business")
    if plan != PlanCode.ENTERPRISE and any(scope.startswith("enterprise:") for scope in scopes):
        raise KeyConstraintError("child_scope_requires_enterprise")


def _requires_human_intent(plan_code: PlanCode, scopes: list[str]) -> bool:
    plan = normalize_plan_code(plan_code)
    return plan_rank(plan) >= plan_rank(PlanCode.PRO) or any(scope.startswith(_HIGH_RISK_SCOPE_PREFIXES) for scope in scopes)
