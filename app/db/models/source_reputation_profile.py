from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class SourceReputationProfile(Base):
    __tablename__ = "source_reputation_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("news_sources.id"), unique=True, index=True)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    signal_quality_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)
    duplication_rate: Mapped[float] = mapped_column(Float, default=0.0)
    false_positive_rate: Mapped[float] = mapped_column(Float, default=0.0)
    first_mover_score: Mapped[float] = mapped_column(Float, default=0.0)
    timeliness_score: Mapped[float] = mapped_column(Float, default=0.0)
    market_relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    security_relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    macro_relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    bitcoin_native_score: Mapped[float] = mapped_column(Float, default=0.0)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    total_articles_seen: Mapped[int] = mapped_column(Integer, default=0)
    total_events_created: Mapped[int] = mapped_column(Integer, default=0)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    notes: Mapped[str] = mapped_column(String(1000), default="")
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
