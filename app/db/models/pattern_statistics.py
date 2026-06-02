from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class PatternStatistics(Base):
    __tablename__ = "pattern_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern_id: Mapped[int] = mapped_column(ForeignKey("market_patterns.id"), unique=True, index=True, nullable=False)
    pattern_slug: Mapped[str] = mapped_column(String(96), index=True, default="")
    historical_occurrences: Mapped[int] = mapped_column(Integer, default=0)
    median_15m_move: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_1h_move: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_4h_move: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_24h_move: Mapped[float | None] = mapped_column(Float, nullable=True)
    positive_rate: Mapped[float] = mapped_column(Float, default=0.0)
    negative_rate: Mapped[float] = mapped_column(Float, default=0.0)
    neutral_rate: Mapped[float] = mapped_column(Float, default=0.0)
    average_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    best_case_move: Mapped[float | None] = mapped_column(Float, nullable=True)
    worst_case_move: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
