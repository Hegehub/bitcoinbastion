from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class CandleAttributionCandidate(Base):
    __tablename__ = "candle_attribution_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candle_id: Mapped[int] = mapped_column(ForeignKey("btc_candles.id"), index=True, nullable=False)
    candidate_type: Mapped[str] = mapped_column(String(64), default="news_event")
    event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), index=True, nullable=True)
    article_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"), index=True, nullable=True)
    raw_score: Mapped[float] = mapped_column(Float, default=0.0)
    normalized_score: Mapped[float] = mapped_column(Float, default=0.0)
    ranking_features_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    rejection_reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
