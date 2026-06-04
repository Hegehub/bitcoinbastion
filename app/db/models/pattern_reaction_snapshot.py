from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class PatternReactionSnapshot(Base):
    __tablename__ = "pattern_reaction_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern_id: Mapped[int] = mapped_column(ForeignKey("market_patterns.id"), index=True, nullable=False)
    occurrence_id: Mapped[int | None] = mapped_column(ForeignKey("pattern_occurrences.id"), nullable=True, index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), nullable=True, index=True)
    reaction_window: Mapped[str] = mapped_column(String(32), default="4h", index=True)
    move_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    direction: Mapped[str] = mapped_column(String(16), default="UNKNOWN", index=True)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reaction_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
