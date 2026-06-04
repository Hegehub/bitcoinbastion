from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class NarrativeMemorySnapshot(Base):
    __tablename__ = "narrative_memory_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    narrative: Mapped[str] = mapped_column(String(96), index=True)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, index=True, default=utcnow)
    event_count: Mapped[int] = mapped_column(Integer, default=0)
    weighted_impact: Mapped[float] = mapped_column(Float, default=0.0)
    source_quality: Mapped[float] = mapped_column(Float, default=0.0)
    market_reaction: Mapped[float] = mapped_column(Float, default=0.0)
    time_decay: Mapped[float] = mapped_column(Float, default=1.0)
    heat_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    strength_score: Mapped[float] = mapped_column(Float, default=0.0)
    decay_score: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
