"""Deterministic Access metric credit-cost model."""

from __future__ import annotations

from app.services.access.metric_catalog import get_metric_definition

BASE_METRIC_COSTS: dict[str, int] = {
    "btc.price": 1,
    "btc.ohlcv": 1,
    "btc.volume": 1,
    "bitcoin.mempool.fee_pressure": 1,
    "bitcoin.fees.estimate": 1,
    "btc.basic_volatility": 2,
    "btc.volatility.regime": 3,
    "btc.trend.regime": 3,
    "btc.liquidity.pressure": 3,
    "bastion.signal.lite_score": 2,
    "bastion.signal.score": 5,
    "bastion.signal.advanced": 10,
    "bastion.historical.similar_patterns": 5,
    "bastion.timemachine.query": 10,
    "trace.address.basic_profile": 5,
    "trace.transaction_graph.summary": 10,
    "trace.advanced.proof_packet": 50,
    "wallet.watch_only.health": 10,
    "wallet.utxo.fragmentation": 10,
    "treasury.read_only.status": 25,
    "payregister.sales_volume": 10,
    "payregister.operator_audit": 25,
    "enterprise.custom.audit_export": 100,
}
DEFAULT_KNOWN_METRIC_COST = 1


def get_metric_cost(metric_name: str) -> int:
    if get_metric_definition(metric_name) is None:
        raise ValueError(f"unknown_metric:{metric_name}")
    return BASE_METRIC_COSTS.get(metric_name, DEFAULT_KNOWN_METRIC_COST)


def validate_known_metrics(metrics: list[str]) -> None:
    for metric_name in metrics:
        if get_metric_definition(metric_name) is None:
            raise ValueError(f"unknown_metric:{metric_name}")


def estimate_query_cost(metrics: list[str], history_days: int | None = None, interval: str | None = None) -> int:
    validate_known_metrics(metrics)
    base_cost = sum(get_metric_cost(metric_name) for metric_name in metrics)
    history_multiplier = _history_multiplier(history_days)
    interval_multiplier = _interval_multiplier(interval)
    return max(1, base_cost * history_multiplier * interval_multiplier)


def _history_multiplier(history_days: int | None) -> int:
    if history_days is None or history_days <= 30:
        return 1
    if history_days <= 365:
        return 2
    if history_days <= 1825:
        return 4
    return 8


def _interval_multiplier(interval: str | None) -> int:
    if interval is None:
        return 1
    normalized = interval.strip().lower()
    if normalized in {"1m", "5m"}:
        return 2
    return 1
