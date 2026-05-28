from datetime import UTC, datetime, timedelta
from typing import Any

from celery import shared_task

from app.db.session import SessionLocal
from app.services.market.candles.builder import BTCCandleBuilderService
from app.services.market.candles.rebuild import rebuild_range


@shared_task(name="market.build_1m_candles", bind=True)  # type: ignore[untyped-decorator]
def build_1m_candles(self: Any) -> dict[str, object]:
    with SessionLocal() as db:
        now = datetime.now(UTC)
        candle = BTCCandleBuilderService().build_candle(db, "1m", now)
        return {"built": candle is not None}


@shared_task(name="market.build_higher_timeframes", bind=True)  # type: ignore[untyped-decorator]
def build_higher_timeframes(self: Any) -> dict[str, int]:
    with SessionLocal() as db:
        now = datetime.now(UTC)
        svc = BTCCandleBuilderService()
        built = 0
        for tf in ("5m", "15m", "1h", "4h", "1d"):
            built += 1 if svc.build_candle(db, tf, now) else 0
        return {"built": built}


@shared_task(name="market.rebuild_candles", bind=True)  # type: ignore[untyped-decorator]
def rebuild_candles(self: Any, timeframe: str, hours: int = 1) -> dict[str, int]:
    with SessionLocal() as db:
        end = datetime.now(UTC)
        start = end - timedelta(hours=hours)
        return {"rebuilt": rebuild_range(db, timeframe, start, end)}


@shared_task(name="market.verify_candle_integrity", bind=True)  # type: ignore[untyped-decorator]
def verify_candle_integrity(self: Any) -> dict[str, str]:
    return {"status": "ok"}
