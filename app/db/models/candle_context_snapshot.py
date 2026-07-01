from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class CandleContextSnapshot(Base):
    __tablename__ = "candle_context_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candle_id: Mapped[int] = mapped_column(ForeignKey("btc_candles.id"), index=True, nullable=False)
    volatility_level: Mapped[str] = mapped_column(String(32), default="unknown")
    volume_level: Mapped[str] = mapped_column(String(32), default="unknown")
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    market_regime: Mapped[str] = mapped_column(String(64), default="unknown")
    news_density: Mapped[int] = mapped_column(Integer, default=0)
    event_density: Mapped[int] = mapped_column(Integer, default=0)
    positive_event_count: Mapped[int] = mapped_column(Integer, default=0)
    negative_event_count: Mapped[int] = mapped_column(Integer, default=0)
    macro_event_count: Mapped[int] = mapped_column(Integer, default=0)
    security_event_count: Mapped[int] = mapped_column(Integer, default=0)
    regulatory_event_count: Mapped[int] = mapped_column(Integer, default=0)
    institutional_event_count: Mapped[int] = mapped_column(Integer, default=0)
    summary_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
