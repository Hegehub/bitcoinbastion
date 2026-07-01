from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class HistoricalSimilarityResult(Base):
    __tablename__ = "historical_similarity_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_events.id"), nullable=True, index=True
    )
    source_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_events.id"), nullable=True, index=True
    )
    reference_signal_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    reference_article_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_articles.id"), nullable=True, index=True
    )
    reference_candle_id: Mapped[int | None] = mapped_column(
        ForeignKey("btc_candles.id"), nullable=True, index=True
    )
    candidate_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_events.id"), nullable=True, index=True
    )
    pattern_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_patterns.id"), nullable=True, index=True
    )
    matched_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_events.id"), nullable=True, index=True
    )
    matched_signal_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    matched_article_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_articles.id"), nullable=True, index=True
    )
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    narrative_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    impact_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    price_behavior_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    reaction_similarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    time_window_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    pattern_type: Mapped[str] = mapped_column(String(64), default="UNKNOWN", index=True)
    reaction_15m_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_1h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_4h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_24h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_direction: Mapped[str] = mapped_column(String(16), default="UNKNOWN")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    explanation_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    limitations_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
