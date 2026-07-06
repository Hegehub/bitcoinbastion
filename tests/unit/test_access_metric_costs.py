from __future__ import annotations

import pytest

from app.services.access.metric_costs import estimate_query_cost, get_metric_cost, validate_known_metrics


def test_unknown_metric_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown_metric"):
        get_metric_cost("unknown.metric")
    with pytest.raises(ValueError, match="unknown_metric"):
        validate_known_metrics(["btc.price", "unknown.metric"])


def test_metric_cost_estimation_is_deterministic() -> None:
    metrics = ["btc.price", "btc.ohlcv", "bastion.signal.score"]

    assert estimate_query_cost(metrics, history_days=30, interval="15m") == estimate_query_cost(
        metrics, history_days=30, interval="15m"
    )


def test_high_cost_metrics_cost_more_than_basic_ohlcv() -> None:
    assert get_metric_cost("trace.advanced.proof_packet") > get_metric_cost("btc.ohlcv")
    assert get_metric_cost("enterprise.custom.audit_export") > get_metric_cost("btc.ohlcv")


def test_historical_query_cost_increases_with_larger_history_range() -> None:
    metrics = ["bastion.historical.similar_patterns"]

    short_cost = estimate_query_cost(metrics, history_days=30, interval="1h")
    long_cost = estimate_query_cost(metrics, history_days=730, interval="1h")

    assert long_cost > short_cost


def test_interval_multiplier_is_deterministic() -> None:
    metrics = ["btc.price"]

    assert estimate_query_cost(metrics, interval="1m") > estimate_query_cost(metrics, interval="1h")
