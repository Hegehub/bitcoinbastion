from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class NarrativeSnapshot(Base):
    __tablename__ = "narrative_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    narrative_id: Mapped[int] = mapped_column(ForeignKey("market_narratives.id"), index=True)
    narrative_type: Mapped[str] = mapped_column(String(64), index=True, default="")
    mention_count: Mapped[int] = mapped_column(Integer, default=0)
    weighted_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    heat_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    velocity_score: Mapped[float] = mapped_column(Float, default=0.0)
    dominance_score: Mapped[float] = mapped_column(Float, default=0.0)
    volume_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    growth_score: Mapped[float] = mapped_column(Float, default=0.0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    event_count: Mapped[int] = mapped_column(Integer, default=0)
    supporting_events_count: Mapped[int] = mapped_column(Integer, default=0)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    trend_direction: Mapped[str] = mapped_column(String(16), default="STABLE", index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
