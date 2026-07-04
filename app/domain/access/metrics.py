"""Metric group constants for Bastion Proof-of-Access Auth."""

from __future__ import annotations

from app.domain.access.plans import PlanCode

MARKET_BASIC = "market.basic"
BITCOIN_NETWORK = "bitcoin.network"
BITCOIN_MEMPOOL = "bitcoin.mempool"
MARKET_INTELLIGENCE = "market.intelligence"
SIGNALS_LITE = "signals.lite"
SIGNALS_STANDARD = "signals.standard"
SIGNALS_ADVANCED = "signals.advanced"
HISTORICAL_SIMILARITY = "historical.similarity"
HISTORICAL_CYCLES = "historical.cycles"
TIMEMACHINE = "timemachine"
TRACE_LITE = "trace.lite"
TRACE_STANDARD = "trace.standard"
TRACE_ADVANCED = "trace.advanced"
PRIVACY_ANALYSIS = "privacy.analysis"
WALLET_HEALTH_BASIC = "wallet.health.basic"
WALLET_HEALTH = "wallet.health"
TREASURY_READ = "treasury.read"
TREASURY_POLICY = "treasury.policy"
PSBT_ANALYSIS = "psbt.analysis"
ACCESS_USAGE = "access.usage"
ACCESS_INTEGRITY = "access.integrity"
PAYREGISTER_METRICS = "payregister.metrics"
PAYREGISTER_OPERATIONS = "payregister.operations"
ENTERPRISE_CUSTOM = "enterprise.custom"

METRIC_GROUPS: frozenset[str] = frozenset(
    {
        MARKET_BASIC,
        BITCOIN_NETWORK,
        BITCOIN_MEMPOOL,
        MARKET_INTELLIGENCE,
        SIGNALS_LITE,
        SIGNALS_STANDARD,
        SIGNALS_ADVANCED,
        HISTORICAL_SIMILARITY,
        HISTORICAL_CYCLES,
        TIMEMACHINE,
        TRACE_LITE,
        TRACE_STANDARD,
        TRACE_ADVANCED,
        PRIVACY_ANALYSIS,
        WALLET_HEALTH_BASIC,
        WALLET_HEALTH,
        TREASURY_READ,
        TREASURY_POLICY,
        PSBT_ANALYSIS,
        ACCESS_USAGE,
        ACCESS_INTEGRITY,
        PAYREGISTER_METRICS,
        PAYREGISTER_OPERATIONS,
        ENTERPRISE_CUSTOM,
    }
)


def metric_group_required_plan(metric_group: str) -> PlanCode:
    """Return the lowest plan that allows a metric group."""

    from app.domain.access.entitlements import required_plan_for_metric_group

    required_plan = required_plan_for_metric_group(metric_group)
    if required_plan is None:
        return PlanCode.ENTERPRISE
    return required_plan
