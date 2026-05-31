from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class HistoricalEventSimilarity(Base):
    __tablename__ = "historical_event_similarities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("news_events.id"), index=True, nullable=False)
    similar_event_id: Mapped[int] = mapped_column(
        ForeignKey("news_events.id"), index=True, nullable=False
    )
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    pattern_match: Mapped[bool] = mapped_column(Boolean, default=False)
    sentiment_match: Mapped[float] = mapped_column(Float, default=0.0)
    impact_match: Mapped[float] = mapped_column(Float, default=0.0)
    volatility_match: Mapped[float] = mapped_column(Float, default=0.0)
    explanation_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
