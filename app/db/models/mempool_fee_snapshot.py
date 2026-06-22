from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class MempoolFeeSnapshot(Base):
    __tablename__ = "mempool_fee_snapshots"
    __table_args__ = (
        Index("ix_mempool_fee_snapshots_source_observed_at", "source", "observed_at"),
        Index("ix_mempool_fee_snapshots_observed_at", "observed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    observed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fastest_fee_sat_vb: Mapped[float | None] = mapped_column(Float, nullable=True)
    half_hour_fee_sat_vb: Mapped[float | None] = mapped_column(Float, nullable=True)
    hour_fee_sat_vb: Mapped[float | None] = mapped_column(Float, nullable=True)
    economy_fee_sat_vb: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_fee_sat_vb: Mapped[float | None] = mapped_column(Float, nullable=True)
    mempool_vsize: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mempool_tx_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
