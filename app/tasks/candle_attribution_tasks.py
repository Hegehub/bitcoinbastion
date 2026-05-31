from datetime import timedelta
from typing import Any

from celery import shared_task
from sqlalchemy import delete, select

from app.db.models.attribution_context_snapshot import AttributionContextSnapshot
from app.db.models.attribution_replay_log import AttributionReplayLog
from app.db.models.btc_candle import BTCCandle
from app.db.models.candle_attribution import CandleAttribution
from app.db.models.candle_attribution_candidate import CandleAttributionCandidate
from app.db.models.candle_context_snapshot import CandleContextSnapshot
from app.db.models.time_utils import utcnow
from app.db.session import SessionLocal
from app.services.intelligence.candle_attribution_engine import CandleAttributionEngine


def _candle_statement(timeframe: str | None, lookback_minutes: int, limit: int, backfill: bool) -> Any:
    stmt = select(BTCCandle).order_by(BTCCandle.open_time.desc()).limit(limit)
    if not backfill:
        cutoff = utcnow() - timedelta(minutes=lookback_minutes)
        stmt = stmt.where(BTCCandle.open_time >= cutoff)
    if timeframe:
        stmt = stmt.where(BTCCandle.timeframe == timeframe)
    return stmt


def _attribute_candles_impl(timeframe: str | None, lookback_minutes: int, limit: int, mode: str) -> dict[str, int]:
    with SessionLocal() as db:
        engine = CandleAttributionEngine(db)
        processed = 0
        attributed = 0
        backfill = mode == "backfill"
        for candle in db.execute(_candle_statement(timeframe, lookback_minutes, limit, backfill)).scalars():
            rows = engine.attribute_candle_object(candle)
            processed += 1
            attributed += len(rows)
        db.commit()
        return {"processed": processed, "attributions": attributed}


@shared_task(name="intelligence.attribute_candles", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})  # type: ignore[untyped-decorator]
def attribute_candles(
    self: Any,
    timeframe: str | None = None,
    lookback_minutes: int = 240,
    limit: int = 100,
    mode: str = "incremental",
) -> dict[str, int]:
    return _attribute_candles_impl(timeframe, lookback_minutes, limit, mode)


@shared_task(name="intelligence.attribute_recent_candles", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})  # type: ignore[untyped-decorator]
def attribute_recent_candles(
    self: Any,
    timeframe: str | None = None,
    lookback_minutes: int = 240,
    limit: int = 100,
) -> dict[str, int]:
    return _attribute_candles_impl(timeframe, lookback_minutes, limit, "incremental")


@shared_task(name="intelligence.rebuild_candle_attributions", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})  # type: ignore[untyped-decorator]
def rebuild_candle_attributions(
    self: Any,
    timeframe: str | None = None,
    lookback_minutes: int = 1440,
    limit: int = 500,
    backfill: bool = False,
) -> dict[str, int]:
    with SessionLocal() as db:
        candles = list(db.execute(_candle_statement(timeframe, lookback_minutes, limit, backfill)).scalars())
        candle_ids = [candle.id for candle in candles]
        if candle_ids:
            db.execute(delete(CandleAttribution).where(CandleAttribution.candle_id.in_(candle_ids)))
            db.execute(delete(CandleAttributionCandidate).where(CandleAttributionCandidate.candle_id.in_(candle_ids)))
            db.execute(delete(AttributionContextSnapshot).where(AttributionContextSnapshot.candle_id.in_(candle_ids)))
            db.execute(delete(CandleContextSnapshot).where(CandleContextSnapshot.candle_id.in_(candle_ids)))
            db.execute(delete(AttributionReplayLog).where(AttributionReplayLog.candle_id.in_(candle_ids)))
        engine = CandleAttributionEngine(db)
        attributed = 0
        for candle in candles:
            attributed += len(engine.attribute_candle_object(candle))
        db.commit()
        return {"processed": len(candles), "attributions": attributed, "rebuilt": len(candle_ids)}


@shared_task(name="intelligence.refresh_candle_context", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})  # type: ignore[untyped-decorator]
def refresh_candle_context(
    self: Any,
    timeframe: str | None = None,
    lookback_minutes: int = 240,
    limit: int = 100,
) -> dict[str, int]:
    with SessionLocal() as db:
        engine = CandleAttributionEngine(db)
        refreshed = 0
        for candle in db.execute(_candle_statement(timeframe, lookback_minutes, limit, False)).scalars():
            db.execute(delete(CandleContextSnapshot).where(CandleContextSnapshot.candle_id == candle.id))
            engine.get_context_snapshot(candle.id)
            refreshed += 1
        db.commit()
        return {"processed": refreshed, "contexts": refreshed}
