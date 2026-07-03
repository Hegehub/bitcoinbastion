from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class NarrativeObservation(Base):
    __tablename__ = "narrative_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    narrative_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    narrative_type: Mapped[str] = mapped_column(String(64), index=True)
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_articles.id"), nullable=True, index=True
    )
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_events.id"), nullable=True, index=True
    )
    observation_score: Mapped[float] = mapped_column(Float, default=0.0)
    strength_score: Mapped[float] = mapped_column(Float, default=0.0)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    source_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    observation_time: Mapped[datetime] = mapped_column(DateTime, index=True, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
