from __future__ import annotations

from datetime import timedelta

from app.db.models.time_utils import utcnow


def default_usage_window(hours: int = 24):
    upper = utcnow()
    return upper - timedelta(hours=hours), upper
