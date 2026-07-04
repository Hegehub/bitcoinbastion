"""Plan limits and metric entitlement helpers for the future Access Policy Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.domain.access.plans import PlanCode, normalize_plan_code, plan_rank
from app.domain.access.scopes import FORBIDDEN_SCOPES
from app.services.access.metric_catalog import (
    get_metric_definition,
    get_metric_group,
    get_metric_group_for_metric,
    list_locked_metric_groups,
    list_metric_groups,
)


@dataclass(frozen=True, slots=True)
class PlanLimits:
    requests_per_minute: int | None
    requests_per_day: int | None
    daily_metric_credits: int | None
    monthly_metric_credits: int | None
    max_history_days: int | None
    min_interval: str | None
    websocket_streams: int | None
    child_api_keys: int | str | None
    delegated_passes: bool | str | int
    offline_validity_pack: bool | str
    batch_query: bool


_PLAN_DISPLAY: dict[PlanCode, dict[str, str]] = {
    PlanCode.LITE: {"name": "Lite", "positioning": "observe"},
    PlanCode.BASIC: {"name": "Basic", "positioning": "use"},
    PlanCode.PLUS: {"name": "Plus", "positioning": "analyze"},
    PlanCode.PRO: {"name": "Pro", "positioning": "automate"},
    PlanCode.BUSINESS: {"name": "Business", "positioning": "operate"},
    PlanCode.ENTERPRISE: {"name": "Enterprise", "positioning": "integrate and control"},
}

_PLAN_LIMITS: dict[PlanCode, PlanLimits] = {
    PlanCode.LITE: PlanLimits(30, 2_000, 1_000, 20_000, 30, "1h", 0, 0, 0, False, False),
    PlanCode.BASIC: PlanLimits(60, 10_000, 10_000, 250_000, 90, "15m", 1, 1, 0, False, False),
    PlanCode.PLUS: PlanLimits(120, 50_000, 50_000, 1_500_000, 730, "5m", 3, 3, 1, "limited_cached", False),
    PlanCode.PRO: PlanLimits(300, 250_000, 250_000, 7_500_000, 1825, "1m", 10, 10, 10, "non_critical_12_24h", True),
    PlanCode.BUSINESS: PlanLimits(600, 1_000_000, 1_000_000, 30_000_000, 1825, "1m", 25, "role_based", "role_based", "shift_based", True),
    PlanCode.ENTERPRISE: PlanLimits(None, None, None, None, None, None, None, "custom", "custom", "custom_policy", True),
}

_PLAN_GROUPS: dict[PlanCode, set[str]] = {
    PlanCode.LITE: {"market.basic", "bitcoin.mempool", "signals.lite", "trace.lite"},
    PlanCode.BASIC: {"market.basic", "bitcoin.network", "bitcoin.mempool", "signals.lite", "trace.lite", "wallet.health"},
    PlanCode.PLUS: {
        "market.basic",
        "bitcoin.network",
        "bitcoin.mempool",
        "market.intelligence",
        "signals.standard",
        "historical.similarity",
        "trace.standard",
        "wallet.health",
        "access.usage",
    },
    PlanCode.PRO: {
        "market.basic",
        "bitcoin.network",
        "bitcoin.mempool",
        "market.intelligence",
        "signals.advanced",
        "historical.similarity",
        "trace.advanced",
        "wallet.health",
        "treasury.read",
        "access.usage",
    },
    PlanCode.BUSINESS: {
        "market.basic",
        "bitcoin.network",
        "bitcoin.mempool",
        "market.intelligence",
        "signals.advanced",
        "historical.similarity",
        "trace.advanced",
        "wallet.health",
        "treasury.read",
        "access.usage",
        "payregister.metrics",
    },
    PlanCode.ENTERPRISE: {
        "market.basic",
        "bitcoin.network",
        "bitcoin.mempool",
        "market.intelligence",
        "signals.advanced",
        "historical.similarity",
        "trace.advanced",
        "wallet.health",
        "treasury.read",
        "access.usage",
        "payregister.metrics",
        "enterprise.custom",
    },
}
_INTERVAL_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "1d": 1440}


def get_plan_limits(plan_code: PlanCode) -> PlanLimits:
    return _PLAN_LIMITS[normalize_plan_code(plan_code)]


def get_plan_metric_groups(plan_code: PlanCode) -> set[str]:
    return set(_PLAN_GROUPS[normalize_plan_code(plan_code)])


def is_metric_group_allowed(plan_code: PlanCode, group_code: str) -> bool:
    if get_metric_group(group_code) is None:
        raise ValueError(f"unknown_metric_group:{group_code}")
    return group_code in get_plan_metric_groups(plan_code)


def is_metric_allowed(plan_code: PlanCode, metric_name: str) -> bool:
    if get_metric_definition(metric_name) is None:
        raise ValueError(f"unknown_metric:{metric_name}")
    group_code = get_metric_group_for_metric(metric_name)
    return group_code is not None and is_metric_group_allowed(plan_code, group_code)


def required_plan_for_metric_group(group_code: str) -> PlanCode | None:
    if get_metric_group(group_code) is None:
        raise ValueError(f"unknown_metric_group:{group_code}")
    for plan in PlanCode:
        if group_code in _PLAN_GROUPS[plan]:
            return plan
    return None


def required_plan_for_metric(metric_name: str) -> PlanCode | None:
    group_code = get_metric_group_for_metric(metric_name)
    if group_code is None:
        raise ValueError(f"unknown_metric:{metric_name}")
    return required_plan_for_metric_group(group_code)


def validate_interval_allowed(plan_code: PlanCode, interval: str) -> bool:
    limits = get_plan_limits(plan_code)
    if limits.min_interval is None:
        return True
    requested = _INTERVAL_MINUTES.get(interval.strip().lower())
    minimum = _INTERVAL_MINUTES[limits.min_interval]
    return requested is not None and requested >= minimum


def validate_history_range_allowed(plan_code: PlanCode, history_days: int) -> bool:
    limits = get_plan_limits(plan_code)
    return limits.max_history_days is None or history_days <= limits.max_history_days


def build_entitlement_overlay(plan_code: PlanCode) -> dict[str, Any]:
    plan = normalize_plan_code(plan_code)
    groups = sorted(get_plan_metric_groups(plan))
    scopes = sorted({scope for group in groups for scope in (get_metric_group(group) or _empty_group()).scopes})
    _validate_no_forbidden_scopes(scopes)
    return {
        "plan_code": plan.value,
        "plan_name": _PLAN_DISPLAY[plan]["name"],
        "positioning": _PLAN_DISPLAY[plan]["positioning"],
        "metric_groups": groups,
        "allowed_scopes": scopes,
        "limits": asdict(get_plan_limits(plan)),
    }


def build_metric_catalog_response(plan_code: PlanCode) -> dict[str, Any]:
    plan = normalize_plan_code(plan_code)
    limits = get_plan_limits(plan)
    available = sorted(get_plan_metric_groups(plan))
    locked = [
        {
            "group_code": locked_group.group_code,
            "required_plan": locked_group.required_plan.value,
            "reason": locked_group.reason,
        }
        for locked_group in list_locked_metric_groups(plan)
    ]
    return {
        "plan": plan.value,
        "available_metric_groups": available,
        "locked_metric_groups": locked,
        "limits": asdict(limits),
        "daily_metric_credits": limits.daily_metric_credits,
        "monthly_metric_credits": limits.monthly_metric_credits,
        "max_history_days": limits.max_history_days,
        "min_interval": limits.min_interval,
        "websocket_streams": limits.websocket_streams,
        "child_api_keys": limits.child_api_keys,
        "delegated_passes": limits.delegated_passes,
        "offline_validity_pack": limits.offline_validity_pack,
        "metric_groups": [
            {
                "code": group.code,
                "name": group.name,
                "metrics": [metric.name for metric in group.metrics],
                "scopes": list(group.scopes),
                "locked": group.code not in available,
            }
            for group in list_metric_groups()
        ],
    }


def _empty_group() -> Any:
    class EmptyGroup:
        scopes: tuple[str, ...] = ()

    return EmptyGroup()


def _validate_no_forbidden_scopes(scopes: list[str]) -> None:
    forbidden = set(scopes) & set(FORBIDDEN_SCOPES)
    if forbidden:
        raise ValueError(f"forbidden_scope:{sorted(forbidden)[0]}")


def plan_supports_at_least(current_plan: PlanCode, required_plan: PlanCode) -> bool:
    return plan_rank(current_plan) >= plan_rank(required_plan)
