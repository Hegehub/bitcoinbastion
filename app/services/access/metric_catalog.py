"""Deterministic metric catalog for Bastion Access entitlements."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.access.plans import PlanCode


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    name: str
    group_code: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class MetricGroup:
    code: str
    name: str
    metrics: tuple[MetricDefinition, ...]
    scopes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LockedMetricGroup:
    group_code: str
    required_plan: PlanCode
    reason: str = "upgrade_required"


def _metric(name: str, group_code: str) -> MetricDefinition:
    return MetricDefinition(name=name, group_code=group_code)


_GROUP_SPECS: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "market.basic",
        "Market Basic",
        ("btc.price", "btc.ohlcv", "btc.volume", "btc.basic_volatility", "btc.basic_trend"),
        ("metrics:basic:read", "market:price:read", "market:ohlcv:read"),
    ),
    (
        "bitcoin.network",
        "Bitcoin Network",
        (
            "bitcoin.block_height",
            "bitcoin.hashrate_estimate",
            "bitcoin.difficulty",
            "bitcoin.transaction_count",
            "bitcoin.block_fullness",
        ),
        ("bitcoin:network:read", "bitcoin:blocks:read"),
    ),
    (
        "bitcoin.mempool",
        "Bitcoin Mempool",
        (
            "bitcoin.mempool.size",
            "bitcoin.mempool.fee_pressure",
            "bitcoin.mempool.confirmation_pressure",
            "bitcoin.fees.estimate",
        ),
        ("bitcoin:mempool:read", "bitcoin:fees:read", "mempool:fees:read"),
    ),
    (
        "market.intelligence",
        "Market Intelligence",
        (
            "btc.volatility.regime",
            "btc.trend.regime",
            "btc.liquidity.pressure",
            "btc.market.structure",
            "btc.momentum.score",
            "btc.correlation.snapshot",
        ),
        (
            "market:intelligence:read",
            "market:volatility:read",
            "market:regime:read",
            "market:liquidity:read",
        ),
    ),
    (
        "signals.lite",
        "Signals Lite",
        (
            "bastion.signal.lite_score",
            "bastion.signal.basic_confidence",
            "bastion.signal.basic_risk_state",
        ),
        ("signals:lite:read",),
    ),
    (
        "signals.standard",
        "Signals Standard",
        (
            "bastion.signal.score",
            "bastion.signal.confidence",
            "bastion.signal.risk_regime",
            "bastion.signal.quarantine_state",
        ),
        ("signals:standard:read", "risk:market:read"),
    ),
    (
        "signals.advanced",
        "Signals Advanced",
        (
            "bastion.signal.advanced",
            "bastion.signal.firewall_state",
            "bastion.signal.anomaly_pressure",
            "bastion.signal.defense_score",
            "bastion.signal.operator_context",
        ),
        ("signals:advanced:read", "risk:market:read"),
    ),
    (
        "historical.similarity",
        "Historical Similarity",
        (
            "bastion.historical.similar_patterns",
            "bastion.historical.cycle_similarity",
            "bastion.historical.drawdown_similarity",
            "bastion.historical.volatility_analogues",
            "bastion.timemachine.query",
        ),
        ("historical:similarity:read", "historical:cycles:read", "timemachine:query"),
    ),
    (
        "trace.lite",
        "Trace Lite",
        ("trace.address.basic_profile", "trace.activity.summary", "trace.privacy.basic_exposure"),
        ("trace:lite:read",),
    ),
    (
        "trace.standard",
        "Trace Standard",
        (
            "trace.transaction_graph.summary",
            "trace.address.activity_profile",
            "trace.flow.direction",
            "trace.coin_age",
            "trace.utxo.behavior",
            "trace.privacy.exposure_score",
            "trace.counterparty.exposure",
        ),
        ("trace:standard:read", "privacy:analysis:read"),
    ),
    (
        "trace.advanced",
        "Trace Advanced",
        (
            "trace.advanced.counterparty_lens",
            "trace.advanced.origin_context",
            "trace.advanced.destination_review",
            "trace.advanced.proof_packet",
            "trace.advanced.business_context",
        ),
        ("trace:advanced:read", "privacy:analysis:advanced", "evidence:packet:create"),
    ),
    (
        "wallet.health",
        "Wallet Health",
        (
            "wallet.watch_only.health",
            "wallet.utxo.fragmentation",
            "wallet.fee_exposure",
            "wallet.address_reuse",
            "wallet.backup_freshness",
            "wallet.policy_compliance",
            "wallet.psbt_readiness",
        ),
        ("wallet:health:read", "psbt:analysis:read"),
    ),
    (
        "treasury.read",
        "Treasury Read",
        (
            "treasury.read_only.status",
            "treasury.policy.summary",
            "treasury.psbt.readiness",
            "treasury.policy.compliance",
        ),
        ("treasury:read", "treasury:policy:read", "psbt:analysis:read"),
    ),
    (
        "access.usage",
        "Access Usage",
        (
            "access.request_count",
            "access.quota_usage",
            "access.active_sessions",
            "access.child_api_keys",
            "access.risk_events",
            "access.failed_signatures",
            "access.revocation_checks",
            "access.integrity_score",
        ),
        ("access:usage:read", "access:integrity:read", "api:keys:read", "api:keys:manage"),
    ),
    (
        "payregister.metrics",
        "PayRegister Metrics",
        (
            "payregister.sales_volume",
            "payregister.paid_invoices",
            "payregister.pending_invoices",
            "payregister.cashier_shift_activity",
            "payregister.device_health",
            "payregister.offline_pack_status",
            "payregister.settlement_status",
            "payregister.refund_events",
            "payregister.operator_audit",
        ),
        (
            "payregister:metrics:read",
            "payregister:operator:read",
            "payregister:admin",
            "payregister:devices:read",
            "payregister:shifts:read",
        ),
    ),
    (
        "enterprise.custom",
        "Enterprise Custom",
        (
            "enterprise.custom.metrics",
            "enterprise.custom.audit_export",
            "enterprise.custom.policy_state",
            "enterprise.custom.revocation_registry",
            "enterprise.custom.transparency_checkpoints",
        ),
        (
            "enterprise:metrics:custom",
            "enterprise:audit:export",
            "enterprise:policy:custom",
            "enterprise:quota:custom",
            "enterprise:private_deployment",
        ),
    ),
)

_METRIC_GROUPS: dict[str, MetricGroup] = {
    code: MetricGroup(
        code=code,
        name=name,
        metrics=tuple(_metric(metric_name, code) for metric_name in metric_names),
        scopes=scopes,
    )
    for code, name, metric_names, scopes in _GROUP_SPECS
}
_METRIC_TO_GROUP: dict[str, str] = {
    metric.name: group.code for group in _METRIC_GROUPS.values() for metric in group.metrics
}


def list_metric_groups() -> list[MetricGroup]:
    return list(_METRIC_GROUPS.values())


def get_metric_group(group_code: str) -> MetricGroup | None:
    return _METRIC_GROUPS.get(group_code)


def get_metric_definition(metric_name: str) -> MetricDefinition | None:
    group_code = get_metric_group_for_metric(metric_name)
    if group_code is None:
        return None
    group = _METRIC_GROUPS[group_code]
    return next(metric for metric in group.metrics if metric.name == metric_name)


def get_metric_group_for_metric(metric_name: str) -> str | None:
    return _METRIC_TO_GROUP.get(metric_name)


def list_metrics_for_group(group_code: str) -> list[MetricDefinition]:
    group = get_metric_group(group_code)
    if group is None:
        return []
    return list(group.metrics)


def list_available_metric_groups(plan_code: PlanCode) -> list[str]:
    from app.services.access.plan_entitlements import get_plan_metric_groups

    return sorted(get_plan_metric_groups(plan_code))


def list_locked_metric_groups(plan_code: PlanCode) -> list[LockedMetricGroup]:
    from app.services.access.plan_entitlements import get_plan_metric_groups, required_plan_for_metric_group

    allowed = get_plan_metric_groups(plan_code)
    locked: list[LockedMetricGroup] = []
    for group_code in _METRIC_GROUPS:
        if group_code in allowed:
            continue
        required_plan = required_plan_for_metric_group(group_code)
        if required_plan is not None:
            locked.append(LockedMetricGroup(group_code=group_code, required_plan=required_plan))
    return locked
