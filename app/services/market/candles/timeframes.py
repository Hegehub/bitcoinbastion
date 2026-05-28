from __future__ import annotations

from datetime import UTC, datetime, timedelta

DURATIONS = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}


def align_window(ts: datetime, timeframe: str) -> tuple[datetime, datetime]:
    t = ts.astimezone(UTC)
    seconds = DURATIONS[timeframe]
    epoch = int(t.timestamp())
    start_epoch = (epoch // seconds) * seconds
    start = datetime.fromtimestamp(start_epoch, tz=UTC)
    end = start + timedelta(seconds=seconds - 1)
    return start, end
