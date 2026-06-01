from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class HistoricalSimilarityRecord(Base):
    __tablename__ = "historical_similarity_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference_event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), nullable=True, index=True)
    reference_article_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"), nullable=True, index=True)
    candidate_event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), nullable=True, index=True)
    candidate_article_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"), nullable=True, index=True)
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    event_type_match: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_match: Mapped[float] = mapped_column(Float, default=0.0)
    impact_match: Mapped[float] = mapped_column(Float, default=0.0)
    narrative_match: Mapped[float] = mapped_column(Float, default=0.0)
    reaction_match: Mapped[float] = mapped_column(Float, default=0.0)
    reaction_15m_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_1h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_4h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_24h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    explanation_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
