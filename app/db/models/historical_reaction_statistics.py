from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class HistoricalReactionStatistics(Base):
    __tablename__ = "historical_reaction_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern_id: Mapped[int] = mapped_column(ForeignKey("market_patterns.id"), unique=True, index=True, nullable=False)
    samples: Mapped[int] = mapped_column(Integer, default=0)
    median_move_15m: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_move_1h: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_move_4h: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_move_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    positive_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    negative_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    neutral_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
