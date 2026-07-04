"""Pure domain layer for Bastion Proof-of-Access Auth."""

from app.domain.access.decisions import AccessDecision, PolicyDecision
from app.domain.access.entitlements import (
    PlanLimits,
    get_plan_limits,
    get_plan_metric_groups,
    get_plan_scopes,
    plan_allows_metric_group,
    plan_allows_scope,
    required_plan_for_metric_group,
    required_plan_for_scope,
)
from app.domain.access.errors import (
    AccessDomainError,
    ForbiddenScopeError,
    InvalidPlanCodeError,
    InvalidScopeError,
    MetricGroupNotAllowedError,
    PlanEntitlementError,
)
from app.domain.access.plans import PlanCode, is_business_or_higher, is_enterprise, normalize_plan_code, plan_rank

__all__ = [
    "AccessDecision",
    "AccessDomainError",
    "ForbiddenScopeError",
    "InvalidPlanCodeError",
    "InvalidScopeError",
    "MetricGroupNotAllowedError",
    "PlanCode",
    "PlanEntitlementError",
    "PlanLimits",
    "PolicyDecision",
    "get_plan_limits",
    "get_plan_metric_groups",
    "get_plan_scopes",
    "is_business_or_higher",
    "is_enterprise",
    "normalize_plan_code",
    "plan_allows_metric_group",
    "plan_allows_scope",
    "plan_rank",
    "required_plan_for_metric_group",
    "required_plan_for_scope",
]
