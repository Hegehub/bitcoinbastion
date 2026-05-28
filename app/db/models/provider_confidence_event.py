from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class ProviderConfidenceEvent(Base):
    __tablename__ = "provider_confidence_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("news_sources.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    old_confidence: Mapped[float] = mapped_column(Float)
    new_confidence: Mapped[float] = mapped_column(Float)
    delta: Mapped[float] = mapped_column(Float)
    reason_code: Mapped[str] = mapped_column(String(64))
    explanation_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
