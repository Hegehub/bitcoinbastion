from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class IntelligenceTimelineEvent(Base):
    __tablename__ = "intelligence_timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    importance: Mapped[str] = mapped_column(String(16), default="MEDIUM")
    visibility: Mapped[str] = mapped_column(String(16), default="INTERNAL")
    source_kind: Mapped[str] = mapped_column(String(32), default="INTERNAL")

    related_article_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"), nullable=True, index=True)
    related_event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), nullable=True, index=True)
    related_signal_id: Mapped[int | None] = mapped_column(ForeignKey("signals.id"), nullable=True, index=True)
    related_candle_id: Mapped[int | None] = mapped_column(ForeignKey("btc_candles.id"), nullable=True, index=True)
    related_provider_id: Mapped[int | None] = mapped_column(ForeignKey("market_provider_health.id"), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(255), default="")
    summary: Mapped[str] = mapped_column(String(1000), default="")

    event_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    btc_price_reference: Mapped[float | None] = mapped_column(Float, nullable=True)
    btc_price_delta_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    timeline_rank: Mapped[float | None] = mapped_column(Float, nullable=True)

    tags_json: Mapped[list[str]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=list)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    evidence_refs_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=list)
    limitations_json: Mapped[list[str]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=list)

    is_replayed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
