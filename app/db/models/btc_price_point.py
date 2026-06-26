from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class BTCPricePoint(Base):
    __tablename__ = "btc_price_points"
    __table_args__ = (
        Index("ix_btc_price_points_pair_observed_at", "pair", "observed_at"),
        Index("ix_btc_price_points_provider_observed_at", "provider", "observed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    provider_name: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(16), default="BTC")
    pair: Mapped[str] = mapped_column(String(16), index=True, default="BTCUSD")
    price_usd: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    raw_payload_hash: Mapped[str] = mapped_column(String(64), index=True)
    aggregation_round_id: Mapped[str] = mapped_column(
        String(64), default="", nullable=False, index=True
    )
    is_median_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
