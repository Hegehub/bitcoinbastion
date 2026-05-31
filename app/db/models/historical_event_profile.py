from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class HistoricalEventProfile(Base):
    __tablename__ = "historical_event_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True, default="unknown")
    pattern_type: Mapped[str] = mapped_column(String(64), index=True, default="UNKNOWN")
    event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), nullable=True, index=True)
    article_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"), nullable=True, index=True)
    canonical_title: Mapped[str] = mapped_column(String(500), default="")
    primary_narrative: Mapped[str] = mapped_column(String(128), default="unknown")
    sentiment_label: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    btc_relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    market_impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    institutional_score: Mapped[float] = mapped_column(Float, default=0.0)
    macro_score: Mapped[float] = mapped_column(Float, default=0.0)
    security_score: Mapped[float] = mapped_column(Float, default=0.0)
    regulatory_score: Mapped[float] = mapped_column(Float, default=0.0)
    sovereignty_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    price_change_15m_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_change_1h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_change_4h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_change_24h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
