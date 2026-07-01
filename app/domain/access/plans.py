"""Plan codes for Bastion Proof-of-Access Auth."""

from __future__ import annotations

from enum import StrEnum

from app.domain.access.errors import InvalidPlanCodeError


class PlanCode(StrEnum):
    """Stable subscription plan codes used by Access entitlements."""

    LITE = "lite_pass"
    BASIC = "basic_pass"
    PLUS = "plus_pass"
    PRO = "pro_pass"
    BUSINESS = "business_pass"
    ENTERPRISE = "enterprise_pass"


_PLAN_RANKS: dict[PlanCode, int] = {
    PlanCode.LITE: 1,
    PlanCode.BASIC: 2,
    PlanCode.PLUS: 3,
    PlanCode.PRO: 4,
    PlanCode.BUSINESS: 5,
    PlanCode.ENTERPRISE: 6,
}


def normalize_plan_code(value: str | PlanCode) -> PlanCode:
    """Return a stable ``PlanCode`` for a string value."""

    if isinstance(value, PlanCode):
        return value
    try:
        return PlanCode(str(value).strip())
    except ValueError as exc:
        raise InvalidPlanCodeError("Invalid access plan code") from exc


def plan_rank(plan: PlanCode) -> int:
    """Return the rank for a plan where larger means more capable."""

    return _PLAN_RANKS[normalize_plan_code(plan)]


def is_business_or_higher(plan: PlanCode) -> bool:
    """Return true for Business and Enterprise plans."""

    return plan_rank(plan) >= plan_rank(PlanCode.BUSINESS)


def is_enterprise(plan: PlanCode) -> bool:
    """Return true only for the Enterprise plan."""

    return normalize_plan_code(plan) is PlanCode.ENTERPRISE
