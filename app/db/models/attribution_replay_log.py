from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class AttributionReplayLog(Base):
    __tablename__ = "attribution_replay_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candle_id: Mapped[int] = mapped_column(ForeignKey("btc_candles.id"), index=True, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), default="candle-attribution-v1")
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    candidate_event_count: Mapped[int] = mapped_column(Integer, default=0)
    timeline_window_before_seconds: Mapped[int] = mapped_column(Integer, default=0)
    timeline_window_after_seconds: Mapped[int] = mapped_column(Integer, default=0)
    ranking_snapshot_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=list)
    explanation_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
