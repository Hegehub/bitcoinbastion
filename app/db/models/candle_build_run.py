from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.models.time_utils import utcnow

class CandleBuildRun(Base):
    __tablename__ = "candle_build_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(8), index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    window_end: Mapped[datetime] = mapped_column(DateTime, index=True)
    source_point_count: Mapped[int] = mapped_column(Integer, default=0)
    provider_count: Mapped[int] = mapped_column(Integer, default=0)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    build_status: Mapped[str] = mapped_column(String(32), default="ok")
    build_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    degraded_reason: Mapped[str] = mapped_column(String(255), default="")
    rebuild_reason: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
