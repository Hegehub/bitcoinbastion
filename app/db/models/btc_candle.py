from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class BTCCandle(Base):
    __tablename__ = "btc_candles"
    __table_args__ = (UniqueConstraint("timeframe", "open_time", name="uq_btc_candles_timeframe_open_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(8), index=True)
    open_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    close_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    open: Mapped[float | None] = mapped_column(Float, nullable=True)
    high: Mapped[float | None] = mapped_column(Float, nullable=True)
    low: Mapped[float | None] = mapped_column(Float, nullable=True)
    close: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_mode: Mapped[str] = mapped_column(String(32), default="median_multi_provider")
    provider_count: Mapped[int] = mapped_column(Integer, default=0)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    provider_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    integrity_status: Mapped[str] = mapped_column(String(32), default="valid", index=True)
    integrity_notes: Mapped[str] = mapped_column(String(500), default="")
    is_partial: Mapped[bool] = mapped_column(Boolean, default=True)
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    rebuild_reason: Mapped[str] = mapped_column(String(255), default="")
    rebuilt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
