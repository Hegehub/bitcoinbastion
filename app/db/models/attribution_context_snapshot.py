from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class AttributionContextSnapshot(Base):
    __tablename__ = "attribution_context_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candle_id: Mapped[int] = mapped_column(ForeignKey("btc_candles.id"), index=True, nullable=False)
    market_volatility: Mapped[float] = mapped_column(Float, default=0.0)
    market_regime: Mapped[str] = mapped_column(String(64), default="unknown")
    provider_health: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    active_news_count: Mapped[int] = mapped_column(Integer, default=0)
    macro_event_count: Mapped[int] = mapped_column(Integer, default=0)
    security_event_count: Mapped[int] = mapped_column(Integer, default=0)
    institutional_event_count: Mapped[int] = mapped_column(Integer, default=0)
    price_provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    news_provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    timeline_snapshot_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
