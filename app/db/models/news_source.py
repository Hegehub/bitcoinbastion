from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class NewsSource(Base):
    __tablename__ = "news_sources"
    __table_args__ = (
        CheckConstraint(
            "credibility_weight >= 0 AND credibility_weight <= 1",
            name="ck_news_sources_credibility_weight",
        ),
        CheckConstraint(
            "signal_quality_weight >= 0 AND signal_quality_weight <= 1",
            name="ck_news_sources_signal_quality_weight",
        ),
        CheckConstraint(
            "sovereignty_weight >= 0 AND sovereignty_weight <= 1",
            name="ck_news_sources_sovereignty_weight",
        ),
        CheckConstraint(
            "default_confidence >= 0 AND default_confidence <= 1",
            name="ck_news_sources_default_confidence",
        ),
        CheckConstraint(
            "fetch_interval_minutes > 0", name="ck_news_sources_fetch_interval_minutes"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid4()), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False, default="rss")
    base_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    rss_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    homepage_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    language: Mapped[str] = mapped_column(String(8), default="en")
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    category: Mapped[str] = mapped_column(
        String(80), nullable=False, default="market_media", index=True
    )
    tier: Mapped[str] = mapped_column(
        String(80), nullable=False, default="market_media", index=True
    )
    credibility_weight: Mapped[float] = mapped_column(Float, default=0.7)
    signal_quality_weight: Mapped[float] = mapped_column(Float, default=0.7)
    sovereignty_weight: Mapped[float] = mapped_column(Float, default=0.7)
    default_confidence: Mapped[float] = mapped_column(Float, default=0.7)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_js_rendering: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_etag: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_last_modified: Mapped[bool] = mapped_column(Boolean, default=False)
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    request_timeout_seconds: Mapped[int] = mapped_column(Integer, default=15)
    backoff_multiplier: Mapped[float] = mapped_column(Float, default=2.0)
    max_failures_before_backoff: Mapped[int] = mapped_column(Integer, default=3)
    notes: Mapped[str] = mapped_column(String(1000), default="")
    tags_json: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_successes: Mapped[int] = mapped_column(Integer, default=0)
    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    backoff_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_degraded: Mapped[bool] = mapped_column(Boolean, default=False)
    health_band: Mapped[str] = mapped_column(String(16), default="UNKNOWN")
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
