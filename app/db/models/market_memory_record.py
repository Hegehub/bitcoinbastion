from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class MarketMemoryRecord(Base):
    __tablename__ = "market_memory_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("news_events.id"), index=True, nullable=False)
    pattern_id: Mapped[int] = mapped_column(
        ForeignKey("market_patterns.id"), index=True, nullable=False
    )
    memory_type: Mapped[str] = mapped_column(String(64), default="historical_context", index=True)
    memory_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
