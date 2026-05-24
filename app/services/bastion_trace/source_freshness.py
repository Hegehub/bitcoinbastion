from datetime import UTC, datetime

from app.schemas.bastion_trace import TraceSourceFreshness


def evaluate_source_freshness(last_refreshed_at: datetime | None, now: datetime | None = None) -> TraceSourceFreshness:
    if last_refreshed_at is None:
        return TraceSourceFreshness.UNKNOWN
    point = now or datetime.now(UTC)
    if last_refreshed_at.tzinfo is None:
        last_refreshed_at = last_refreshed_at.replace(tzinfo=UTC)
    age_days = (point - last_refreshed_at).total_seconds() / 86400
    if age_days <= 1:
        return TraceSourceFreshness.FRESH
    if age_days <= 7:
        return TraceSourceFreshness.RECENT
    return TraceSourceFreshness.STALE
