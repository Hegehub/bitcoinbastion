from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class ProviderHealthTimeSeriesSnapshot(Base):
    __tablename__ = "provider_health_timeseries_snapshots"
    __table_args__ = (
        Index("ix_provider_health_ts_provider_observed", "provider_key", "observed_at"),
        Index("ix_provider_health_ts_domain_observed", "domain", "observed_at"),
        Index("ix_provider_health_ts_status_observed", "status", "observed_at"),
        Index("ix_provider_health_ts_degraded_observed", "is_degraded", "observed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    provider_key: Mapped[str] = mapped_column(String(120), index=True)
    source_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    domain: Mapped[str] = mapped_column(String(64), default="generic", index=True)
    status: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    health_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    degraded_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    runtime_mode: Mapped[str] = mapped_column(String(32), default="normal", index=True)
    is_degraded: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SourceHealthTimeSeriesSnapshot(Base):
    __tablename__ = "source_health_timeseries_snapshots"
    __table_args__ = (
        Index("ix_source_health_ts_source_observed", "source_key", "observed_at"),
        Index("ix_source_health_ts_provider_observed", "provider_key", "observed_at"),
        Index("ix_source_health_ts_domain_observed", "domain", "observed_at"),
        Index("ix_source_health_ts_status_observed", "status", "observed_at"),
        Index("ix_source_health_ts_degraded_observed", "is_degraded", "observed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    provider_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    source_key: Mapped[str] = mapped_column(String(120), index=True)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    domain: Mapped[str] = mapped_column(String(64), default="generic", index=True)
    status: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    health_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    degraded_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    runtime_mode: Mapped[str] = mapped_column(String(32), default="normal", index=True)
    is_degraded: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ProviderConfidenceTimeSeriesEvent(Base):
    __tablename__ = "provider_confidence_timeseries_events"
    __table_args__ = (
        Index("ix_provider_confidence_ts_provider_observed", "provider_key", "observed_at"),
        Index("ix_provider_confidence_ts_domain_observed", "domain", "observed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    provider_key: Mapped[str] = mapped_column(String(120), index=True)
    source_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    domain: Mapped[str] = mapped_column(String(64), default="generic", index=True)
    event_type: Mapped[str] = mapped_column(String(64), default="confidence_changed", index=True)
    previous_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="recorded", index=True)
    is_degraded: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SourceConfidenceTimeSeriesEvent(Base):
    __tablename__ = "source_confidence_timeseries_events"
    __table_args__ = (
        Index("ix_source_confidence_ts_source_observed", "source_key", "observed_at"),
        Index("ix_source_confidence_ts_domain_observed", "domain", "observed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    provider_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    source_key: Mapped[str] = mapped_column(String(120), index=True)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    domain: Mapped[str] = mapped_column(String(64), default="generic", index=True)
    event_type: Mapped[str] = mapped_column(String(64), default="confidence_changed", index=True)
    previous_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="recorded", index=True)
    is_degraded: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
