from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class PatternReactionProfile(Base):
    __tablename__ = "pattern_reaction_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern_id: Mapped[int] = mapped_column(
        ForeignKey("market_patterns.id"), index=True, nullable=False
    )
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    median_change_15m: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_change_1h: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_change_4h: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_change_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_change_15m: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_change_1h: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_change_4h: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_change_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
