from datetime import UTC, datetime, timedelta
from typing import Any
from celery import shared_task
from app.db.session import SessionLocal
from app.services.market.candle_builder import MarketCandleBuilderService

@shared_task(name="market.build_candles", bind=True)  # type: ignore[untyped-decorator]
def build_candles(self: Any, timeframe: str = "1m") -> dict[str, object]:
    with SessionLocal() as db:
        c = MarketCandleBuilderService().build(db, timeframe, datetime.now(UTC))
        return {"built": c is not None}

@shared_task(name="market.rebuild_candles", bind=True)  # type: ignore[untyped-decorator]
def rebuild_candles(self: Any, timeframe: str = "1m", hours: int = 1) -> dict[str, int]:
    with SessionLocal() as db:
        svc = MarketCandleBuilderService()
        now = datetime.now(UTC)
        cur = now - timedelta(hours=hours)
        n = 0
        while cur <= now:
            n += 1 if svc.build(db, timeframe, cur) else 0
            cur += timedelta(minutes=1)
        return {"rebuilt": n}

@shared_task(name="market.refresh_market_context", bind=True)  # type: ignore[untyped-decorator]
def refresh_market_context(self: Any) -> dict[str, str]:
    return {"status": "ok"}
