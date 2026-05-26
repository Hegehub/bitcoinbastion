from fastapi import APIRouter, Depends
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
    return {"data": [{"timeframe": r.timeframe, "open_time": r.open_time, "close_time": r.close_time, "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume, "provider_count": r.provider_count, "provider_confidence": r.provider_confidence, "integrity_status": r.integrity_status, "is_partial": r.is_partial, "is_finalized": r.is_finalized, "source_mode": r.source_mode} for r in rows]}


@router.get("/btc/candles/{timeframe}/latest")
def btc_candles_latest(timeframe: str, db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.btc_candle import BTCCandle

    row = db.execute(select(BTCCandle).where(BTCCandle.timeframe == timeframe).order_by(BTCCandle.open_time.desc()).limit(1)).scalar_one_or_none()
    if row is None:
        return {"data": None}
    return {"data": {"timeframe": row.timeframe, "open_time": row.open_time, "close_time": row.close_time, "open": row.open, "high": row.high, "low": row.low, "close": row.close, "volume": row.volume, "provider_count": row.provider_count, "provider_confidence": row.provider_confidence, "integrity_status": row.integrity_status, "is_partial": row.is_partial, "is_finalized": row.is_finalized, "source_mode": row.source_mode}}


@router.get("/btc/candles/latest")
def btc_candles_latest_any(db: Session = Depends(db_session), timeframe: str = "1m") -> dict[str, object]:
    return btc_candles_latest(timeframe=timeframe, db=db)
