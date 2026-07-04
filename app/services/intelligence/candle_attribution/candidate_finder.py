from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.btc_candle import BTCCandle
from app.db.models.news_event import NewsEvent


class CandidateEventFinder:
    """Find replay-safe news-event candidates around a BTC candle."""

    def __init__(self) -> None:
        settings = get_settings()
        self.window_before_minutes = int(settings.attribution_window_before_minutes)
        self.window_after_minutes = int(settings.attribution_window_after_minutes)

    def find_candidates(
        self, db: Session, candle: BTCCandle, limit: int | None = None
    ) -> list[NewsEvent]:
        start = candle.open_time - timedelta(minutes=self.window_before_minutes)
        end = candle.close_time + timedelta(minutes=self.window_after_minutes)
        stmt = (
            select(NewsEvent)
            .where(NewsEvent.first_seen_at <= end)
            .where(NewsEvent.last_seen_at >= start)
            .order_by(
                NewsEvent.btc_relevance_score.desc(),
                NewsEvent.market_impact_score.desc(),
                NewsEvent.id.desc(),
            )
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(db.execute(stmt).scalars())
