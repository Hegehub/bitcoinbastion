from fastapi import APIRouter, Depends
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.services.market.collector import BTCPriceCollector
from app.services.market.context import BTCMarketContextService

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/btc/price")
def btc_price(db: Session = Depends(db_session)) -> dict[str, object]:
    context = BTCMarketContextService().get_current_context(db)
    return {"data": context}


@router.get("/btc/providers")
def btc_providers(db: Session = Depends(db_session)) -> dict[str, object]:
    rows = BTCPriceCollector().providers_health(db)
    return {"data": [{"provider_name": r.provider_name, "provider_confidence": r.provider_confidence, "is_degraded": r.is_degraded} for r in rows]}


@router.get("/btc/context")
def btc_context(db: Session = Depends(db_session)) -> dict[str, object]:
    return {"data": BTCMarketContextService().get_current_context(db)}


@router.get("/providers/health")
def providers_health(db: Session = Depends(db_session)) -> dict[str, object]:
    rows = BTCPriceCollector().providers_health(db)
    return {"data": [{"provider_name": r.provider_name, "last_success_at": r.last_success_at, "last_failure_at": r.last_failure_at, "failure_count": r.failure_count, "success_count": r.success_count, "consecutive_failures": r.consecutive_failures, "avg_latency_ms": r.avg_latency_ms, "provider_confidence": r.provider_confidence, "is_degraded": r.is_degraded} for r in rows]}


@router.get("/btc/candles")
def btc_candles(timeframe: str, db: Session = Depends(db_session), start: str | None = None, end: str | None = None, limit: int = 200) -> dict[str, object]:
    from datetime import datetime
    from sqlalchemy import select
    from app.db.models.btc_candle import BTCCandle

    q = select(BTCCandle).where(BTCCandle.timeframe == timeframe).order_by(BTCCandle.open_time.desc()).limit(limit)
    if start:
        q = q.where(BTCCandle.open_time >= datetime.fromisoformat(start))
    if end:
        q = q.where(BTCCandle.open_time <= datetime.fromisoformat(end))
    rows = list(db.execute(q).scalars())
    return {"data": [{"timeframe": r.timeframe, "open_time": r.open_time, "close_time": r.close_time, "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume, "provider_count": r.provider_count, "provider_confidence": r.provider_confidence, "integrity_status": r.integrity_status, "is_partial": r.is_partial, "is_finalized": r.is_finalized, "price_source_mode": r.price_source_mode} for r in rows]}


@router.get("/btc/candles/{timeframe}/latest")
def btc_candles_latest(timeframe: str, db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.btc_candle import BTCCandle

    row = db.execute(select(BTCCandle).where(BTCCandle.timeframe == timeframe).order_by(BTCCandle.open_time.desc()).limit(1)).scalar_one_or_none()
    if row is None:
        return {"data": None}
    return {"data": {"timeframe": row.timeframe, "open_time": row.open_time, "close_time": row.close_time, "open": row.open, "high": row.high, "low": row.low, "close": row.close, "volume": row.volume, "provider_count": row.provider_count, "provider_confidence": row.provider_confidence, "integrity_status": row.integrity_status, "is_partial": row.is_partial, "is_finalized": row.is_finalized, "price_source_mode": row.price_source_mode}}


@router.get("/btc/candles/latest")
def btc_candles_latest_any(db: Session = Depends(db_session), timeframe: str = "1m") -> dict[str, object]:
    return btc_candles_latest(timeframe=timeframe, db=db)


@router.get("/btc/candles/{candle_id}")
def btc_candle_by_id(candle_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    from app.db.models.btc_candle import BTCCandle
    row = db.get(BTCCandle, candle_id)
    return {"data": None if row is None else {"id": row.id, "timeframe": row.timeframe, "open_time": row.open_time, "close_time": row.close_time, "open": row.open, "high": row.high, "low": row.low, "close": row.close, "provider_confidence": row.provider_confidence, "provider_count": row.provider_count, "market_regime": row.market_regime, "volatility_score": row.volatility_score, "is_degraded": row.is_degraded}}

@router.get("/btc/candles/{candle_id}/evidence")
def btc_candle_evidence(candle_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.candle_provider_snapshot import CandleProviderSnapshot
    rows = list(db.execute(select(CandleProviderSnapshot).where(CandleProviderSnapshot.candle_id == candle_id)).scalars())
    return {"data": [{"provider_name": r.provider_name, "open": r.provider_price_open, "high": r.provider_price_high, "low": r.provider_price_low, "close": r.provider_price_close, "provider_confidence": r.provider_confidence} for r in rows]}

@router.get("/health")
def market_health(db: Session = Depends(db_session)) -> dict[str, object]:
    from datetime import UTC, datetime
    from statistics import median
    from sqlalchemy import select
    from app.db.models.market_provider_health import MarketProviderHealth

    try:
        rows = list(db.execute(select(MarketProviderHealth)).scalars())
    except OperationalError:
        return {"data": {"provider_count": 0, "healthy_provider_count": 0, "degraded_provider_count": 0, "failed_provider_count": 0, "global_market_confidence": 0.0, "median_provider_latency_ms": 0.0, "stale_provider_count": 0, "generated_at": datetime.now(UTC), "limitations": ["market_provider_health_table_unavailable"]}}
    lats = [r.avg_latency_ms for r in rows if r.avg_latency_ms is not None]
    degraded = [r for r in rows if r.is_degraded]
    failed = [r for r in rows if r.failure_count > r.success_count and r.failure_count > 0]
    healthy = [r for r in rows if not r.is_degraded]
    conf = sum((r.provider_confidence for r in rows), 0.0) / len(rows) if rows else 0.0
    return {"data": {"provider_count": len(rows), "healthy_provider_count": len(healthy), "degraded_provider_count": len(degraded), "failed_provider_count": len(failed), "global_market_confidence": round(conf, 4), "median_provider_latency_ms": float(median(lats)) if lats else 0.0, "stale_provider_count": 0, "generated_at": datetime.now(UTC), "limitations": []}}


@router.get("/btc/price/history")
def btc_price_history(db: Session = Depends(db_session), limit: int = 200) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.btc_price_point import BTCPricePoint

    try:
        rows = list(db.execute(select(BTCPricePoint).order_by(BTCPricePoint.observed_at.desc()).limit(limit)).scalars())
    except OperationalError:
        return {"data": []}
    return {"data": [{"provider_name": r.provider_name or r.provider, "provider_kind": "MARKET_PROVIDER", "symbol": r.symbol, "pair": r.pair, "price_usd": r.price_usd, "observed_at": r.observed_at, "provider_confidence": r.provider_confidence, "provider_latency_ms": r.provider_latency_ms or r.latency_ms, "provider_status": r.metadata_json.get("provider_status", "healthy"), "limitations": []} for r in rows]}
