from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class NewsEvent(Base):
    __tablename__ = "news_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid4()), unique=True, nullable=False)
    event_key: Mapped[str] = mapped_column(String(128), index=True, default="")
    canonical_title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(500), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    canonical_summary: Mapped[str] = mapped_column(Text, default="")
    event_type: Mapped[str] = mapped_column(String(64), index=True, default="unknown")
    event_category: Mapped[str] = mapped_column(String(64), index=True, default="unknown")
    primary_article_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime)
    source_count: Mapped[int] = mapped_column(Integer, default=1)
    article_count: Mapped[int] = mapped_column(Integer, default=1)
    cluster_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    btc_relevance_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    market_impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    event_sentiment: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    event_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    event_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_label: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    first_source_id: Mapped[int | None] = mapped_column(ForeignKey("news_sources.id"), nullable=True)
    first_source_name: Mapped[str] = mapped_column(String(255), default="")
    first_source_published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dominant_language: Mapped[str] = mapped_column(String(16), default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_high_impact: Mapped[bool] = mapped_column(Boolean, default=False)
    is_security_related: Mapped[bool] = mapped_column(Boolean, default=False)
    is_regulatory_related: Mapped[bool] = mapped_column(Boolean, default=False)
    is_macro_related: Mapped[bool] = mapped_column(Boolean, default=False)
    is_institutional_related: Mapped[bool] = mapped_column(Boolean, default=False)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    limitations_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
