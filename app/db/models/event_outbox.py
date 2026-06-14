from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class EventOutboxStatus(StrEnum):
    PENDING = "pending"
    LOCKED = "locked"
    DISPATCHED = "dispatched"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


EVENT_OUTBOX_STATUSES = {status.value for status in EventOutboxStatus}


class EventOutbox(Base):
    __tablename__ = "event_outbox"
    __table_args__ = (
        Index("ix_event_outbox_event_id", "event_id", unique=True),
        Index("ix_event_outbox_status", "status"),
        Index("ix_event_outbox_event_type", "event_type"),
        Index("ix_event_outbox_domain", "domain"),
        Index("ix_event_outbox_aggregate", "aggregate_type", "aggregate_id"),
        Index("ix_event_outbox_next_attempt_at", "next_attempt_at"),
        Index("ix_event_outbox_created_at", "created_at"),
        Index("ix_event_outbox_status_next_attempt", "status", "next_attempt_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_type: Mapped[str] = mapped_column(String(160), nullable=False)
    event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    domain: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    aggregate_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=EventOutboxStatus.PENDING.value
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dead_lettered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
