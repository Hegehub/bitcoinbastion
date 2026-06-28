"""API routes for bounded Market Time Machine analytics queries."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.core.config import get_settings
from app.services.market_time_machine import (
    MarketTimeMachineAnalyticsResponse,
    MarketTimeMachineAnalyticsService,
)
from app.storage.analytics_store.health import build_analytics_store

router = APIRouter(prefix="/market-time-machine", tags=["market-time-machine"])


def get_market_time_machine_service() -> MarketTimeMachineAnalyticsService:
    return MarketTimeMachineAnalyticsService(build_analytics_store(get_settings()))


@router.get("/events", response_model=MarketTimeMachineAnalyticsResponse)
async def market_events(
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    asset: str = Query("BTC", min_length=1, max_length=12),
    limit: int = Query(500, ge=1, le=5000),
    event_type: str | None = Query(None, min_length=1, max_length=160),
    service: MarketTimeMachineAnalyticsService = Depends(get_market_time_machine_service),
) -> MarketTimeMachineAnalyticsResponse:
    return await service.get_market_event_timeline(
        from_ts=from_ts, to_ts=to_ts, asset=asset, limit=limit, event_type=event_type
    )


@router.get("/news-impact", response_model=MarketTimeMachineAnalyticsResponse)
async def news_impact(
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    asset: str = Query("BTC", min_length=1, max_length=12),
    source: str | None = Query(None, min_length=1, max_length=160),
    limit: int = Query(500, ge=1, le=5000),
    service: MarketTimeMachineAnalyticsService = Depends(get_market_time_machine_service),
) -> MarketTimeMachineAnalyticsResponse:
    return await service.get_news_impact_history(
        from_ts=from_ts, to_ts=to_ts, asset=asset, source=source, limit=limit
    )


@router.get("/candle-attribution", response_model=MarketTimeMachineAnalyticsResponse)
async def candle_attribution(
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    asset: str = Query("BTC", min_length=1, max_length=12),
    interval: str = Query("1h", min_length=1, max_length=16),
    limit: int = Query(500, ge=1, le=5000),
    service: MarketTimeMachineAnalyticsService = Depends(get_market_time_machine_service),
) -> MarketTimeMachineAnalyticsResponse:
    return await service.get_candle_attribution_history(
        from_ts=from_ts, to_ts=to_ts, asset=asset, interval=interval, limit=limit
    )


@router.get("/provider-degradation", response_model=MarketTimeMachineAnalyticsResponse)
async def provider_degradation(
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    provider: str | None = Query(None, min_length=1, max_length=160),
    limit: int = Query(500, ge=1, le=5000),
    service: MarketTimeMachineAnalyticsService = Depends(get_market_time_machine_service),
) -> MarketTimeMachineAnalyticsResponse:
    return await service.get_provider_degradation_history(
        from_ts=from_ts, to_ts=to_ts, provider=provider, limit=limit
    )


@router.get("/signal-reliability", response_model=MarketTimeMachineAnalyticsResponse)
async def signal_reliability(
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    asset: str = Query("BTC", min_length=1, max_length=12),
    min_confidence: float | None = Query(None, ge=0, le=1),
    limit: int = Query(500, ge=1, le=5000),
    service: MarketTimeMachineAnalyticsService = Depends(get_market_time_machine_service),
) -> MarketTimeMachineAnalyticsResponse:
    return await service.get_signal_reliability_history(
        from_ts=from_ts,
        to_ts=to_ts,
        asset=asset,
        min_confidence=min_confidence,
        limit=limit,
    )


@router.get("/regime-transitions", response_model=MarketTimeMachineAnalyticsResponse)
async def regime_transitions(
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    asset: str = Query("BTC", min_length=1, max_length=12),
    regime: str | None = Query(None, min_length=1, max_length=64),
    limit: int = Query(500, ge=1, le=5000),
    service: MarketTimeMachineAnalyticsService = Depends(get_market_time_machine_service),
) -> MarketTimeMachineAnalyticsResponse:
    return await service.get_market_regime_transitions(
        from_ts=from_ts, to_ts=to_ts, asset=asset, regime=regime, limit=limit
    )


@router.get("/reaction-windows", response_model=MarketTimeMachineAnalyticsResponse)
async def reaction_windows(
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    asset: str = Query("BTC", min_length=1, max_length=12),
    source: str | None = Query(None, min_length=1, max_length=160),
    limit: int = Query(500, ge=1, le=5000),
    service: MarketTimeMachineAnalyticsService = Depends(get_market_time_machine_service),
) -> MarketTimeMachineAnalyticsResponse:
    return await service.get_historical_reaction_windows(
        from_ts=from_ts, to_ts=to_ts, asset=asset, source=source, limit=limit
    )
