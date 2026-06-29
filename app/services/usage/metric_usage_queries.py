from __future__ import annotations

from datetime import datetime, timedelta

from app.db.models.time_utils import utcnow


def default_usage_window(hours: int = 24) -> tuple[datetime, datetime]:
    upper = utcnow()
    return upper - timedelta(hours=hours), upper
