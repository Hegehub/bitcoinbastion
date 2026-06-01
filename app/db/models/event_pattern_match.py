from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class EventPatternMatch(Base):
    __tablename__ = "event_pattern_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("news_events.id"), index=True, nullable=False)
    pattern_id: Mapped[int] = mapped_column(
        ForeignKey("market_patterns.id"), index=True, nullable=False
    )
    classification_confidence: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    reasons_json: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
