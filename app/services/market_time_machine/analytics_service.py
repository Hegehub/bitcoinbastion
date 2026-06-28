"""Market Time Machine analytics service backed by ClickHouse projections."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from app.storage.analytics_store.base import AnalyticsStore
from app.storage.analytics_store.errors import AnalyticsStoreDisabledError, AnalyticsStoreError
from app.storage.analytics_store.schemas import AnalyticsStoreStatusValue
from app.services.market_time_machine import queries
from app.services.market_time_machine.schemas import (
    CandleAttributionHistoryItem,
    HistoricalReactionWindowItem,
    MarketEventTimelineItem,
    MarketRegimeTransitionItem,
    MarketTimeMachineAnalyticsResponse,
    MarketTimeMachineQueryMeta,
    MarketTimeMachineQueryWindow,
    MarketTimeMachineRuntimeMode,
    MarketTimeMachineSourceStore,
    NewsImpactHistoryItem,
    ProviderDegradationHistoryItem,
    SignalReliabilityHistoryItem,
    default_query_window,
)

MAX_WINDOW_DAYS_DEFAULT = 365
MAX_WINDOW_DAYS_HARD = 3650
DEFAULT_LIMIT = 500
MAX_LIMIT = 5000

ItemFactory = Callable[[dict[str, object]], BaseModel]


class MarketTimeMachineAnalyticsService:
    def __init__(self, analytics_store: AnalyticsStore) -> None:
        self.analytics_store = analytics_store

    async def get_market_event_timeline(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        asset: str = "BTC",
        limit: int = DEFAULT_LIMIT,
        event_type: str | None = None,
    ) -> MarketTimeMachineAnalyticsResponse:
        window, limit = self._normalize_bounds(from_ts, to_ts, limit)
        query = queries.market_event_timeline_query(
            from_ts=window.from_ts,
            to_ts=window.to_ts,
            asset=self._normalize_asset(asset),
            limit=limit,
            event_type=event_type,
        )
        return await self._execute(query, window, limit, MarketEventTimelineItem)

    async def get_news_impact_history(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        asset: str = "BTC",
        limit: int = DEFAULT_LIMIT,
        source: str | None = None,
    ) -> MarketTimeMachineAnalyticsResponse:
        window, limit = self._normalize_bounds(from_ts, to_ts, limit)
        query = queries.news_impact_history_query(
            from_ts=window.from_ts,
            to_ts=window.to_ts,
            asset=self._normalize_asset(asset),
            limit=limit,
            source=source,
        )
        return await self._execute(query, window, limit, NewsImpactHistoryItem)

    async def get_candle_attribution_history(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        asset: str = "BTC",
        interval: str = "1h",
        limit: int = DEFAULT_LIMIT,
    ) -> MarketTimeMachineAnalyticsResponse:
        window, limit = self._normalize_bounds(from_ts, to_ts, limit)
        query = queries.candle_attribution_history_query(
            from_ts=window.from_ts,
            to_ts=window.to_ts,
            asset=self._normalize_asset(asset),
            interval=interval,
            limit=limit,
        )
        return await self._execute(query, window, limit, CandleAttributionHistoryItem)

    async def get_provider_degradation_history(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        provider: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> MarketTimeMachineAnalyticsResponse:
        window, limit = self._normalize_bounds(from_ts, to_ts, limit)
        query = queries.provider_degradation_history_query(
            from_ts=window.from_ts,
            to_ts=window.to_ts,
            provider=provider,
            limit=limit,
        )
        return await self._execute(query, window, limit, ProviderDegradationHistoryItem)

    async def get_signal_reliability_history(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        asset: str = "BTC",
        min_confidence: float | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> MarketTimeMachineAnalyticsResponse:
        window, limit = self._normalize_bounds(from_ts, to_ts, limit)
        query = queries.signal_reliability_history_query(
            from_ts=window.from_ts,
            to_ts=window.to_ts,
            asset=self._normalize_asset(asset),
            min_confidence=min_confidence,
            limit=limit,
        )
        return await self._execute(query, window, limit, SignalReliabilityHistoryItem)

    async def get_market_regime_transitions(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        asset: str = "BTC",
        regime: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> MarketTimeMachineAnalyticsResponse:
        window, limit = self._normalize_bounds(from_ts, to_ts, limit)
        query = queries.market_regime_transitions_query(
            from_ts=window.from_ts,
            to_ts=window.to_ts,
            asset=self._normalize_asset(asset),
            regime=regime,
            limit=limit,
        )
        return await self._execute(query, window, limit, MarketRegimeTransitionItem)

    async def get_historical_reaction_windows(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        asset: str = "BTC",
        source: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> MarketTimeMachineAnalyticsResponse:
        window, limit = self._normalize_bounds(from_ts, to_ts, limit)
        query = queries.historical_reaction_windows_query(
            from_ts=window.from_ts,
            to_ts=window.to_ts,
            asset=self._normalize_asset(asset),
            source=source,
            limit=limit,
        )
        return await self._execute(query, window, limit, HistoricalReactionWindowItem)

    async def _execute(
        self,
        query: queries.AnalyticsQuery,
        window: MarketTimeMachineQueryWindow,
        limit: int,
        item_factory: type[BaseModel],
    ) -> MarketTimeMachineAnalyticsResponse:
        bounds_response = self._bounds_response(window, limit)
        if bounds_response is not None:
            return bounds_response

        started_at = time.monotonic()
        health = await self.analytics_store.healthcheck()
        if health.status == AnalyticsStoreStatusValue.DISABLED:
            return _empty_response(
                window,
                limit,
                MarketTimeMachineRuntimeMode.DISABLED,
                MarketTimeMachineSourceStore.NONE,
                warnings=["clickhouse_disabled"],
                limitations=["historical_analytics_unavailable_without_clickhouse"],
            )
        if health.status != AnalyticsStoreStatusValue.OK:
            return _empty_response(
                window,
                limit,
                MarketTimeMachineRuntimeMode.UNAVAILABLE,
                MarketTimeMachineSourceStore.NONE,
                warnings=["clickhouse_unavailable"],
                limitations=["analytics_projection_store_unavailable"],
            )

        try:
            result = await self.analytics_store.execute(query.query, query.params)
        except AnalyticsStoreDisabledError:
            return _empty_response(
                window,
                limit,
                MarketTimeMachineRuntimeMode.DISABLED,
                MarketTimeMachineSourceStore.NONE,
                warnings=["clickhouse_disabled"],
                limitations=["historical_analytics_unavailable_without_clickhouse"],
            )
        except AnalyticsStoreError:
            return _empty_response(
                window,
                limit,
                MarketTimeMachineRuntimeMode.DEGRADED,
                MarketTimeMachineSourceStore.CLICKHOUSE,
                warnings=["projection_missing"],
                limitations=["requested_projection_not_available_yet"],
            )
        except Exception:  # noqa: BLE001 - service boundary degrades low-level store errors.
            return _empty_response(
                window,
                limit,
                MarketTimeMachineRuntimeMode.UNAVAILABLE,
                MarketTimeMachineSourceStore.NONE,
                warnings=["clickhouse_unavailable"],
                limitations=["analytics_projection_store_unavailable"],
            )

        items = [item_factory(**row) for row in result.rows]
        meta = MarketTimeMachineQueryMeta(
            runtime_mode=MarketTimeMachineRuntimeMode.LIVE,
            source_store=MarketTimeMachineSourceStore.CLICKHOUSE,
            window=window,
            limit=limit,
            warnings=[] if window.days <= MAX_WINDOW_DAYS_DEFAULT else ["large_query_window"],
            limitations=(
                [] if window.days <= MAX_WINDOW_DAYS_DEFAULT else ["large_windows_may_be_slower"]
            ),
            runtime_ms=round((time.monotonic() - started_at) * 1000, 3),
        )
        return MarketTimeMachineAnalyticsResponse.from_meta(meta, items)

    def _normalize_bounds(
        self, from_ts: datetime | None, to_ts: datetime | None, limit: int
    ) -> tuple[MarketTimeMachineQueryWindow, int]:
        if from_ts is None and to_ts is None:
            window = default_query_window()
        else:
            upper = _aware(to_ts or datetime.now(UTC))
            lower = _aware(from_ts or (upper - timedelta(days=1)))
            window = MarketTimeMachineQueryWindow(from_ts=lower, to_ts=upper)
        normalized_limit = min(max(1, limit), MAX_LIMIT)
        return window, normalized_limit

    def _bounds_response(
        self, window: MarketTimeMachineQueryWindow, limit: int
    ) -> MarketTimeMachineAnalyticsResponse | None:
        if window.from_ts > window.to_ts:
            return _empty_response(
                window,
                limit,
                MarketTimeMachineRuntimeMode.DEGRADED,
                MarketTimeMachineSourceStore.NONE,
                warnings=["invalid_query_window"],
                limitations=["from_ts_must_be_before_to_ts"],
            )
        if window.days > MAX_WINDOW_DAYS_HARD:
            return _empty_response(
                window,
                limit,
                MarketTimeMachineRuntimeMode.DEGRADED,
                MarketTimeMachineSourceStore.NONE,
                warnings=["query_window_too_large"],
                limitations=[f"max_allowed_days={MAX_WINDOW_DAYS_HARD}"],
            )
        return None

    def _normalize_asset(self, asset: str) -> str:
        candidate = (asset or "BTC").strip().upper()
        return "BTC" if candidate != "BTC" else candidate


def _empty_response(
    window: MarketTimeMachineQueryWindow,
    limit: int,
    mode: MarketTimeMachineRuntimeMode,
    source_store: MarketTimeMachineSourceStore,
    *,
    warnings: list[str],
    limitations: list[str],
) -> MarketTimeMachineAnalyticsResponse:
    meta = MarketTimeMachineQueryMeta(
        runtime_mode=mode,
        source_store=source_store,
        window=window,
        limit=limit,
        warnings=warnings,
        limitations=limitations,
    )
    return MarketTimeMachineAnalyticsResponse.from_meta(meta, [])


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
