from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.services.market.candles.builder import BTCCandleBuilderService
from app.services.market.candles.timeframes import DURATIONS


def rebuild_range(db: Session, timeframe: str, start: datetime, end: datetime) -> int:
    svc = BTCCandleBuilderService()
    step = timedelta(seconds=DURATIONS[timeframe])
    current = start
    count = 0
    while current <= end:
        if svc.rebuild_candle(db, timeframe, current):
            count += 1
        current += step
    return count
