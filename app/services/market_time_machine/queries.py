"""Parameterized ClickHouse query builders for Market Time Machine analytics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AnalyticsQuery:
    query: str
    params: dict[str, Any]
    table: str


def market_event_timeline_query(
    *, from_ts: datetime, to_ts: datetime, asset: str, limit: int, event_type: str | None = None
) -> AnalyticsQuery:
    query = """
        SELECT event_id, event_type, occurred_at, asset, timeframe, regime,
               confidence_band, signal_family, payload_json
        FROM market_time_machine_events
        WHERE occurred_at >= {from_ts:DateTime64(3)}
          AND occurred_at <= {to_ts:DateTime64(3)}
          AND asset = {asset:String}
          AND ({event_type:String} = '' OR event_type = {event_type:String})
        ORDER BY occurred_at DESC
        LIMIT {limit:UInt32}
    """
    return AnalyticsQuery(
        query=query,
        params=_params(from_ts, to_ts, asset, limit, event_type),
        table="market_time_machine_events",
    )


def news_impact_history_query(
    *, from_ts: datetime, to_ts: datetime, asset: str, limit: int, source: str | None = None
) -> AnalyticsQuery:
    query = """
        SELECT event_id, occurred_at, asset, impact_window, source_tier,
               confidence_score, impact_score, sentiment_band, payload_json
        FROM news_impact_events
        WHERE occurred_at >= {from_ts:DateTime64(3)}
          AND occurred_at <= {to_ts:DateTime64(3)}
          AND asset = {asset:String}
          AND ({source:String} = '' OR source_hash = {source:String})
        ORDER BY occurred_at DESC
        LIMIT {limit:UInt32}
    """
    return AnalyticsQuery(
        query=query,
        params=_params(from_ts, to_ts, asset, limit, source=source),
        table="news_impact_events",
    )


def candle_attribution_history_query(
    *, from_ts: datetime, to_ts: datetime, asset: str, interval: str, limit: int
) -> AnalyticsQuery:
    query = """
        SELECT event_id, asset, timeframe, candle_open_time, candidate_type,
               candidate_rank, attribution_score, confidence_score, payload_json
        FROM candle_attribution_events
        WHERE candle_open_time >= {from_ts:DateTime64(3)}
          AND candle_open_time <= {to_ts:DateTime64(3)}
          AND asset = {asset:String}
          AND timeframe = {interval:String}
        ORDER BY candle_open_time DESC, candidate_rank ASC
        LIMIT {limit:UInt32}
    """
    return AnalyticsQuery(
        query=query,
        params=_params(from_ts, to_ts, asset, limit, interval=interval),
        table="candle_attribution_events",
    )


def provider_degradation_history_query(
    *, from_ts: datetime, to_ts: datetime, provider: str | None, limit: int
) -> AnalyticsQuery:
    query = """
        SELECT event_id, occurred_at, object_hash AS provider, risk_band, decision, payload_json
        FROM operator_replay_events
        WHERE occurred_at >= {from_ts:DateTime64(3)}
          AND occurred_at <= {to_ts:DateTime64(3)}
          AND operator_event_type = 'provider.health.event'
          AND ({provider:String} = '' OR object_hash = {provider:String})
        ORDER BY occurred_at DESC
        LIMIT {limit:UInt32}
    """
    return AnalyticsQuery(
        query=query,
        params=_params(from_ts, to_ts, "BTC", limit, provider=provider),
        table="operator_replay_events",
    )


def signal_reliability_history_query(
    *, from_ts: datetime, to_ts: datetime, asset: str, limit: int, min_confidence: float | None
) -> AnalyticsQuery:
    query = """
        SELECT event_id, occurred_at, signal_family, confidence_band, payload_json
        FROM market_time_machine_events
        WHERE occurred_at >= {from_ts:DateTime64(3)}
          AND occurred_at <= {to_ts:DateTime64(3)}
          AND asset = {asset:String}
          AND ({min_confidence:Float64} <= 0 OR confidence_band != '')
        ORDER BY occurred_at DESC
        LIMIT {limit:UInt32}
    """
    return AnalyticsQuery(
        query=query,
        params=_params(from_ts, to_ts, asset, limit, min_confidence=min_confidence or 0),
        table="market_time_machine_events",
    )


def market_regime_transitions_query(
    *, from_ts: datetime, to_ts: datetime, asset: str, regime: str | None, limit: int
) -> AnalyticsQuery:
    query = """
        SELECT event_id, occurred_at, asset, regime, confidence_band, payload_json
        FROM market_time_machine_events
        WHERE occurred_at >= {from_ts:DateTime64(3)}
          AND occurred_at <= {to_ts:DateTime64(3)}
          AND asset = {asset:String}
          AND ({regime:String} = '' OR regime = {regime:String})
        ORDER BY occurred_at DESC
        LIMIT {limit:UInt32}
    """
    return AnalyticsQuery(
        query=query,
        params=_params(from_ts, to_ts, asset, limit, regime=regime),
        table="market_time_machine_events",
    )


def historical_reaction_windows_query(
    *, from_ts: datetime, to_ts: datetime, asset: str, limit: int, source: str | None = None
) -> AnalyticsQuery:
    query = """
        SELECT event_id, occurred_at, asset, impact_window, price_move_bps,
               volume_change_bps, volatility_change_bps, payload_json
        FROM news_impact_events
        WHERE occurred_at >= {from_ts:DateTime64(3)}
          AND occurred_at <= {to_ts:DateTime64(3)}
          AND asset = {asset:String}
          AND ({source:String} = '' OR source_hash = {source:String})
        ORDER BY occurred_at DESC
        LIMIT {limit:UInt32}
    """
    return AnalyticsQuery(
        query=query,
        params=_params(from_ts, to_ts, asset, limit, source=source),
        table="news_impact_events",
    )


def _params(
    from_ts: datetime,
    to_ts: datetime,
    asset: str,
    limit: int,
    event_type: str | None = None,
    source: str | None = None,
    interval: str | None = None,
    provider: str | None = None,
    regime: str | None = None,
    min_confidence: float = 0,
) -> dict[str, Any]:
    return {
        "from_ts": from_ts,
        "to_ts": to_ts,
        "asset": asset.upper(),
        "limit": limit,
        "event_type": event_type or "",
        "source": source or "",
        "interval": interval or "",
        "provider": provider or "",
        "regime": regime or "",
        "min_confidence": min_confidence,
    }
