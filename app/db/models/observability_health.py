from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow

HEALTH_STATES = {"healthy", "degraded", "critical", "maintenance", "offline"}


class SystemHealthSnapshot(Base):
    __tablename__ = "system_health_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    system_state: Mapped[str] = mapped_column(String(24), index=True, default="healthy")
    summary: Mapped[str] = mapped_column(String(500), default="")
    degraded_count: Mapped[int] = mapped_column(Integer, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    fallback_active: Mapped[bool] = mapped_column(Boolean, default=False)
    operator_attention_required: Mapped[bool] = mapped_column(Boolean, default=False)
    snapshot_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class ProviderHealthSnapshot(Base):
    __tablename__ = "provider_health_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(120), index=True)
    provider_type: Mapped[str] = mapped_column(String(64), index=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    backoff_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    health_state: Mapped[str] = mapped_column(String(24), index=True, default="healthy")
    details_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class BackgroundJobHealth(Base):
    __tablename__ = "background_job_health"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_name: Mapped[str] = mapped_column(String(160), index=True)
    last_start_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_finish_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    failure_reason: Mapped[str] = mapped_column(Text, default="")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    next_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    worker_name: Mapped[str] = mapped_column(String(120), default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ServiceHealthSnapshot(Base):
    __tablename__ = "service_health_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_name: Mapped[str] = mapped_column(String(120), index=True)
    health_state: Mapped[str] = mapped_column(String(24), index=True, default="healthy")
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class RuntimeStateSnapshot(Base):
    __tablename__ = "runtime_state_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    system_state: Mapped[str] = mapped_column(String(24), index=True, default="healthy")
    provider_state: Mapped[str] = mapped_column(String(24), default="healthy")
    job_state: Mapped[str] = mapped_column(String(24), default="healthy")
    signal_pipeline_state: Mapped[str] = mapped_column(String(24), default="healthy")
    evidence_pipeline_state: Mapped[str] = mapped_column(String(24), default="healthy")
    telegram_state: Mapped[str] = mapped_column(String(24), default="healthy")
    state_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class DegradedComponentSnapshot(Base):
    __tablename__ = "degraded_component_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    severity: Mapped[str] = mapped_column(String(24), index=True)
    affected_component: Mapped[str] = mapped_column(String(160), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    recommendation: Mapped[str] = mapped_column(Text, default="")
    automatic_fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    operator_attention_required: Mapped[bool] = mapped_column(Boolean, default=True)
    details_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class RecoveryEvent(Base):
    __tablename__ = "recovery_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    component: Mapped[str] = mapped_column(String(160), index=True)
    failure_time: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    fallback_activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    recovery_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    automatic: Mapped[bool] = mapped_column(Boolean, default=True)
    operator_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(40), default="failure_detected", index=True)
    details_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
