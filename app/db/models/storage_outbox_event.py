from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class StorageOutboxEventStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    RETRY = "retry"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class StorageOutboxEvent(Base):
    __tablename__ = "storage_outbox_events"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_storage_outbox_events_event_id"),
        UniqueConstraint("idempotency_key", name="uq_storage_outbox_events_idempotency_key"),
        Index("ix_storage_outbox_status_available_at", "status", "available_at"),
        Index("ix_storage_outbox_event_type", "event_type"),
        Index("ix_storage_outbox_aggregate", "aggregate_type", "aggregate_id"),
        Index("ix_storage_outbox_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(80), nullable=False)
    event_type: Mapped[str] = mapped_column(String(160), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(120), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(160), nullable=False)
    aggregate_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False, default=dict
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False, default=dict
    )
    target_stores: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False, default=list
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=StorageOutboxEventStatus.PENDING.value
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    locked_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    available_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )
