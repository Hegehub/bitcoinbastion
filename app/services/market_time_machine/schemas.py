"""Schemas for Market Time Machine analytics responses."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class MarketTimeMachineRuntimeMode(StrEnum):
    LIVE = "live"
    DEGRADED = "degraded"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"


class MarketTimeMachineSourceStore(StrEnum):
    CLICKHOUSE = "clickhouse"
    POSTGRES_FALLBACK = "postgres_fallback"
    NONE = "none"


class MarketTimeMachineQueryWindow(BaseModel):
    from_ts: datetime
    to_ts: datetime

    @field_validator("from_ts", "to_ts")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    @property
    def days(self) -> float:
        return (self.to_ts - self.from_ts).total_seconds() / 86_400


class MarketTimeMachineQueryMeta(BaseModel):
    runtime_mode: MarketTimeMachineRuntimeMode
    source_store: MarketTimeMachineSourceStore
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    window: MarketTimeMachineQueryWindow
    limit: int
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    runtime_ms: float | None = None


class MarketEventTimelineItem(BaseModel):
    event_id: str
    event_type: str | None = None
    occurred_at: datetime | None = None
    asset: str | None = None
    timeframe: str | None = None
    regime: str | None = None
    confidence_band: str | None = None
    signal_family: str | None = None
    payload_json: str | None = None


class NewsImpactHistoryItem(BaseModel):
    event_id: str
    occurred_at: datetime | None = None
    asset: str | None = None
    impact_window: str | None = None
    source_tier: str | None = None
    confidence_score: float | None = None
    impact_score: float | None = None
    sentiment_band: str | None = None
    payload_json: str | None = None


class CandleAttributionHistoryItem(BaseModel):
    event_id: str
    asset: str | None = None
    timeframe: str | None = None
    candle_open_time: datetime | None = None
    candidate_type: str | None = None
    candidate_rank: int | None = None
    attribution_score: float | None = None
    confidence_score: float | None = None
    payload_json: str | None = None


class ProviderDegradationHistoryItem(BaseModel):
    event_id: str
    occurred_at: datetime | None = None
    provider: str | None = None
    risk_band: str | None = None
    decision: str | None = None
    payload_json: str | None = None


class SignalReliabilityHistoryItem(BaseModel):
    event_id: str
    occurred_at: datetime | None = None
    signal_family: str | None = None
    confidence_band: str | None = None
    payload_json: str | None = None


class MarketRegimeTransitionItem(BaseModel):
    event_id: str
    occurred_at: datetime | None = None
    asset: str | None = None
    regime: str | None = None
    confidence_band: str | None = None
    payload_json: str | None = None


class HistoricalReactionWindowItem(BaseModel):
    event_id: str
    occurred_at: datetime | None = None
    asset: str | None = None
    impact_window: str | None = None
    price_move_bps: float | None = None
    volume_change_bps: float | None = None
    volatility_change_bps: float | None = None
    payload_json: str | None = None


class MarketTimeMachineAnalyticsResponse(BaseModel):
    runtime_mode: MarketTimeMachineRuntimeMode
    source_store: MarketTimeMachineSourceStore
    generated_at: datetime
    window: MarketTimeMachineQueryWindow
    items: list[dict[str, Any]] = Field(default_factory=list)
    limit: int
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    runtime_ms: float | None = None

    @classmethod
    def from_meta(
        cls,
        meta: MarketTimeMachineQueryMeta,
        items: list[BaseModel] | None = None,
    ) -> "MarketTimeMachineAnalyticsResponse":
        return cls(
            runtime_mode=meta.runtime_mode,
            source_store=meta.source_store,
            generated_at=meta.generated_at,
            window=meta.window,
            items=[item.model_dump(mode="json") for item in (items or [])],
            limit=meta.limit,
            warnings=meta.warnings,
            limitations=meta.limitations,
            runtime_ms=meta.runtime_ms,
        )


def default_query_window(now: datetime | None = None) -> MarketTimeMachineQueryWindow:
    upper = now or datetime.now(UTC)
    if upper.tzinfo is None:
        upper = upper.replace(tzinfo=UTC)
    return MarketTimeMachineQueryWindow(from_ts=upper - timedelta(days=1), to_ts=upper)
