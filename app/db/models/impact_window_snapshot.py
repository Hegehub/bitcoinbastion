from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class ImpactWindowSnapshot(Base):
    __tablename__ = "impact_window_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    impact_id: Mapped[int] = mapped_column(ForeignKey("news_price_impacts.id"), index=True, nullable=False)
    window_name: Mapped[str] = mapped_column(String(16), index=True)
    window_minutes: Mapped[int] = mapped_column(Integer)
    price_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    absolute_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    volatility_score: Mapped[float] = mapped_column(Float, default=0.0)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    direction_match: Mapped[str] = mapped_column(String(16), default="unknown")
    window_weight: Mapped[float] = mapped_column(Float, default=0.0)
    degraded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
