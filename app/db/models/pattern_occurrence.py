from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class PatternOccurrence(Base):
    __tablename__ = "pattern_occurrences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern_id: Mapped[int] = mapped_column(
        ForeignKey("market_patterns.id"), index=True, nullable=False
    )
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_articles.id"), nullable=True, index=True
    )
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_events.id"), nullable=True, index=True
    )
    impact_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_price_impacts.id"), nullable=True, index=True
    )
    attribution_id: Mapped[int | None] = mapped_column(
        ForeignKey("candle_attributions.id"), nullable=True, index=True
    )
    signal_id: Mapped[int | None] = mapped_column(
        ForeignKey("intelligence_signal_candidates.id"), nullable=True, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    classification_reason: Mapped[str] = mapped_column(String(1000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
