from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class HistoricalSimilarityMatch(Base):
    __tablename__ = "historical_similarity_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("news_events.id"), index=True, nullable=False)
    reference_occurrence_id: Mapped[int | None] = mapped_column(ForeignKey("pattern_occurrences.id"), index=True, nullable=True)
    candidate_occurrence_id: Mapped[int | None] = mapped_column(ForeignKey("pattern_occurrences.id"), index=True, nullable=True)
    similar_event_id: Mapped[int] = mapped_column(ForeignKey("news_events.id"), index=True, nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    pattern_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    market_context_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    time_distance_days: Mapped[float] = mapped_column(Float, default=0.0)
    reaction_similarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    time_structure_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_match: Mapped[float] = mapped_column(Float, default=0.0)
    direction_match: Mapped[float] = mapped_column(Float, default=0.0)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    explanation_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
