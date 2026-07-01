"""Default plan entitlements for Bastion Proof-of-Access Auth."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.access.errors import ForbiddenScopeError, InvalidScopeError, MetricGroupNotAllowedError
from app.domain.access.metrics import (
    ACCESS_INTEGRITY,
    ACCESS_USAGE,
    BITCOIN_MEMPOOL as METRIC_BITCOIN_MEMPOOL,
    BITCOIN_NETWORK as METRIC_BITCOIN_NETWORK,
    ENTERPRISE_CUSTOM,
    HISTORICAL_CYCLES,
    HISTORICAL_SIMILARITY,
    MARKET_BASIC,
    MARKET_INTELLIGENCE,
    METRIC_GROUPS,
    PAYREGISTER_METRICS,
    PAYREGISTER_OPERATIONS,
    PRIVACY_ANALYSIS,
    PSBT_ANALYSIS,
    SIGNALS_ADVANCED,
    SIGNALS_LITE,
    SIGNALS_STANDARD,
    TIMEMACHINE,
    TRACE_ADVANCED,
    TRACE_LITE,
    TRACE_STANDARD,
    TREASURY_POLICY,
    TREASURY_READ as METRIC_TREASURY_READ,
    WALLET_HEALTH,
    WALLET_HEALTH_BASIC as METRIC_WALLET_HEALTH_BASIC,
)
from app.domain.access.plans import PlanCode, normalize_plan_code, plan_rank
from app.domain.access.scopes import (
    ACCESS_INTEGRITY_READ,
    ACCESS_SCOPES,
    ACCESS_USAGE_READ,
    ALERTS_MANAGE,
    API_KEYS_MANAGE,
    API_KEYS_READ,
    API_READ,
    BITCOIN_FEES_READ,
    BITCOIN_MEMPOOL_READ,
    BITCOIN_NETWORK_READ,
    BUSINESS_AUDIT_READ,
    BUSINESS_ROLES_MANAGE,
    BUSINESS_WORKSPACE,
    DELEGATED_PASS_CREATE,
    ENTERPRISE_AUDIT_EXPORT,
    ENTERPRISE_METRICS_CUSTOM,
    ENTERPRISE_POLICY_CUSTOM,
    ENTERPRISE_PRIVATE_DEPLOYMENT,
    ENTERPRISE_QUOTA_CUSTOM,
    ENTERPRISE_WORKSPACE,
    EVIDENCE_PACKET_CREATE,
    FORBIDDEN_SCOPES,
    HISTORICAL_CYCLES_READ,
    HISTORICAL_SIMILARITY_READ,
    MARKET_INTELLIGENCE_READ,
    MARKET_LIQUIDITY_READ,
    MARKET_OHLCV_READ,
    MARKET_PRICE_READ,
    MARKET_REGIME_READ,
    MARKET_VOLATILITY_READ,
    METRICS_BASIC_READ,
    PAYREGISTER_ADMIN,
    PAYREGISTER_DEVICES_READ,
    PAYREGISTER_INVOICES_READ,
    PAYREGISTER_METRICS_READ,
    PAYREGISTER_OPERATOR_READ,
    PAYREGISTER_SHIFTS_READ,
    PRIVACY_ANALYSIS_ADVANCED,
    PRIVACY_ANALYSIS_READ,
    PSBT_ANALYSIS_READ,
    SIGNALS_ADVANCED_READ,
    SIGNALS_LITE_READ,
    SIGNALS_STANDARD_READ,
    TIMEMACHINE_QUERY,
    TRACE_ADVANCED_READ,
    TRACE_LITE_READ,
    TRACE_STANDARD_READ,
    TRANSPARENCY_CHECKPOINT_READ,
    TREASURY_POLICY_READ,
    TREASURY_READ,
    WALLET_HEALTH_BASIC,
    WALLET_HEALTH_READ,
)


@dataclass(frozen=True, slots=True)
class PlanLimits:
    """Default request and metric limits for a plan.

    ``None`` means the value is custom for Enterprise entitlements.
    """

    requests_per_minute: int | None
    requests_per_day: int | None
    max_history_days: int | None
    min_interval: str | None
    websocket_streams: int | None
    child_api_keys: int | None
    daily_metric_credits: int | None
    monthly_metric_credits: int | None


_LITE_SCOPES = frozenset(
    {
        METRICS_BASIC_READ,
        MARKET_PRICE_READ,
        MARKET_OHLCV_READ,
        BITCOIN_MEMPOOL_READ,
        BITCOIN_FEES_READ,
        SIGNALS_LITE_READ,
        TRACE_LITE_READ,
    }
)
_BASIC_SCOPES = _LITE_SCOPES | frozenset({BITCOIN_NETWORK_READ, MARKET_VOLATILITY_READ, WALLET_HEALTH_BASIC, API_READ})
_PLUS_SCOPES = _BASIC_SCOPES | frozenset(
    {
        MARKET_INTELLIGENCE_READ,
        MARKET_REGIME_READ,
        MARKET_LIQUIDITY_READ,
        SIGNALS_STANDARD_READ,
        HISTORICAL_SIMILARITY_READ,
        TRACE_STANDARD_READ,
        PRIVACY_ANALYSIS_READ,
        WALLET_HEALTH_READ,
        ACCESS_INTEGRITY_READ,
        ALERTS_MANAGE,
    }
)
_PRO_SCOPES = _PLUS_SCOPES | frozenset(
    {
        SIGNALS_ADVANCED_READ,
        HISTORICAL_CYCLES_READ,
        TIMEMACHINE_QUERY,
        TRACE_ADVANCED_READ,
        PRIVACY_ANALYSIS_ADVANCED,
        TREASURY_READ,
        TREASURY_POLICY_READ,
        PSBT_ANALYSIS_READ,
        API_KEYS_READ,
        API_KEYS_MANAGE,
        DELEGATED_PASS_CREATE,
        EVIDENCE_PACKET_CREATE,
    }
)
_BUSINESS_SCOPES = _PRO_SCOPES | frozenset(
    {
        BUSINESS_WORKSPACE,
        BUSINESS_AUDIT_READ,
        BUSINESS_ROLES_MANAGE,
        PAYREGISTER_METRICS_READ,
        PAYREGISTER_OPERATOR_READ,
        PAYREGISTER_DEVICES_READ,
        PAYREGISTER_SHIFTS_READ,
        PAYREGISTER_INVOICES_READ,
        ACCESS_USAGE_READ,
    }
)
_ENTERPRISE_SCOPES = _BUSINESS_SCOPES | frozenset(
    {
        ENTERPRISE_WORKSPACE,
        ENTERPRISE_POLICY_CUSTOM,
        ENTERPRISE_QUOTA_CUSTOM,
        ENTERPRISE_METRICS_CUSTOM,
        ENTERPRISE_AUDIT_EXPORT,
        ENTERPRISE_PRIVATE_DEPLOYMENT,
        PAYREGISTER_ADMIN,
        TRANSPARENCY_CHECKPOINT_READ,
    }
)

_PLAN_SCOPES: dict[PlanCode, frozenset[str]] = {
    PlanCode.LITE: _LITE_SCOPES,
    PlanCode.BASIC: _BASIC_SCOPES,
    PlanCode.PLUS: _PLUS_SCOPES,
    PlanCode.PRO: _PRO_SCOPES,
    PlanCode.BUSINESS: _BUSINESS_SCOPES,
    PlanCode.ENTERPRISE: _ENTERPRISE_SCOPES,
}

_LITE_METRIC_GROUPS = frozenset({MARKET_BASIC, METRIC_BITCOIN_MEMPOOL, SIGNALS_LITE, TRACE_LITE})
_BASIC_METRIC_GROUPS = _LITE_METRIC_GROUPS | frozenset({METRIC_BITCOIN_NETWORK, METRIC_WALLET_HEALTH_BASIC})
_PLUS_METRIC_GROUPS = _BASIC_METRIC_GROUPS | frozenset(
    {
        MARKET_INTELLIGENCE,
        SIGNALS_STANDARD,
        HISTORICAL_SIMILARITY,
        TRACE_STANDARD,
        PRIVACY_ANALYSIS,
        WALLET_HEALTH,
        ACCESS_INTEGRITY,
    }
)
_PRO_METRIC_GROUPS = _PLUS_METRIC_GROUPS | frozenset(
    {SIGNALS_ADVANCED, HISTORICAL_CYCLES, TIMEMACHINE, TRACE_ADVANCED, METRIC_TREASURY_READ, TREASURY_POLICY, PSBT_ANALYSIS}
)
_BUSINESS_METRIC_GROUPS = _PRO_METRIC_GROUPS | frozenset({ACCESS_USAGE, PAYREGISTER_METRICS, PAYREGISTER_OPERATIONS})
_ENTERPRISE_METRIC_GROUPS = _BUSINESS_METRIC_GROUPS | frozenset({ENTERPRISE_CUSTOM})

_PLAN_METRIC_GROUPS: dict[PlanCode, frozenset[str]] = {
    PlanCode.LITE: _LITE_METRIC_GROUPS,
    PlanCode.BASIC: _BASIC_METRIC_GROUPS,
    PlanCode.PLUS: _PLUS_METRIC_GROUPS,
    PlanCode.PRO: _PRO_METRIC_GROUPS,
    PlanCode.BUSINESS: _BUSINESS_METRIC_GROUPS,
    PlanCode.ENTERPRISE: _ENTERPRISE_METRIC_GROUPS,
}

_PLAN_LIMITS: dict[PlanCode, PlanLimits] = {
    PlanCode.LITE: PlanLimits(30, 2_000, 30, "1h", 0, 0, 1_000, 20_000),
    PlanCode.BASIC: PlanLimits(60, 10_000, 90, "15m", 1, 1, 10_000, 250_000),
    PlanCode.PLUS: PlanLimits(120, 50_000, 730, "5m", 3, 3, 50_000, 1_500_000),
    PlanCode.PRO: PlanLimits(300, 250_000, 1_825, "1m", 10, 10, 250_000, 7_500_000),
    PlanCode.BUSINESS: PlanLimits(600, 1_000_000, 3_650, "1m", 25, 50, 1_000_000, 30_000_000),
    PlanCode.ENTERPRISE: PlanLimits(None, None, None, None, None, None, None, None),
}


def _validate_entitlements() -> None:
    for scopes in _PLAN_SCOPES.values():
        forbidden = scopes & FORBIDDEN_SCOPES
        if forbidden:
            raise ForbiddenScopeError("Forbidden scope present in plan entitlement")
        unknown = scopes - ACCESS_SCOPES
        if unknown:
            raise InvalidScopeError("Unknown scope present in plan entitlement")
    for metric_groups in _PLAN_METRIC_GROUPS.values():
        if unknown := metric_groups - METRIC_GROUPS:
            raise MetricGroupNotAllowedError("Unknown metric group present in plan entitlement")


_validate_entitlements()


def get_plan_scopes(plan: PlanCode) -> frozenset[str]:
    """Return the default scopes for a plan."""

    return _PLAN_SCOPES[normalize_plan_code(plan)]


def get_plan_metric_groups(plan: PlanCode) -> frozenset[str]:
    """Return the default metric groups for a plan."""

    return _PLAN_METRIC_GROUPS[normalize_plan_code(plan)]


def get_plan_limits(plan: PlanCode) -> PlanLimits:
    """Return default limits for a plan."""

    return _PLAN_LIMITS[normalize_plan_code(plan)]


def plan_allows_scope(plan: PlanCode, scope: str) -> bool:
    """Return true when a plan includes a scope."""

    if scope in FORBIDDEN_SCOPES:
        return False
    return scope in get_plan_scopes(plan)


def plan_allows_metric_group(plan: PlanCode, metric_group: str) -> bool:
    """Return true when a plan includes a metric group."""

    return metric_group in get_plan_metric_groups(plan)


def required_plan_for_scope(scope: str) -> PlanCode | None:
    """Return the lowest plan that includes a scope, or ``None`` if unknown."""

    if scope in FORBIDDEN_SCOPES:
        return None
    for plan in sorted(PlanCode, key=plan_rank):
        if scope in _PLAN_SCOPES[plan]:
            return plan
    return None


def required_plan_for_metric_group(metric_group: str) -> PlanCode | None:
    """Return the lowest plan that includes a metric group, or ``None`` if unknown."""

    for plan in sorted(PlanCode, key=plan_rank):
        if metric_group in _PLAN_METRIC_GROUPS[plan]:
            return plan
    return None
