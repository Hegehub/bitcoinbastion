from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class HistoricalReactionProfile(Base):
    __tablename__ = "historical_reaction_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("news_events.id"), index=True, nullable=False)
    reaction_15m_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_1h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_4h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reaction_24h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_positive_move_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_negative_move_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    volatility_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
