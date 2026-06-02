from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class MarketMemoryOperatorReview(Base):
    __tablename__ = "market_memory_operator_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("news_events.id"), index=True, nullable=False)
    pattern_id: Mapped[int | None] = mapped_column(ForeignKey("market_patterns.id"), index=True, nullable=True)
    similar_event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    override_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(String(1000), default="")
    false_similarity: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    audit_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
