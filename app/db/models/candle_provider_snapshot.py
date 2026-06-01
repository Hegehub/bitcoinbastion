from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.models.time_utils import utcnow

class CandleProviderSnapshot(Base):
    __tablename__ = "candle_provider_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candle_id: Mapped[int] = mapped_column(ForeignKey("btc_candles.id"), index=True)
    provider_name: Mapped[str] = mapped_column(String(32), index=True)
    provider_price_open: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_price_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_price_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_price_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    provider_health_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
