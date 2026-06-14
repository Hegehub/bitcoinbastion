from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class WebhookEndpointStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    FAILING = "failing"
    DELETED = "deleted"


class WebhookDeliveryStatus(StrEnum):
    PENDING = "pending"
    TEST_CREATED = "test_created"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    RETRY_SCHEDULED = "retry_scheduled"
    DEAD = "dead"
    SKIPPED = "skipped"


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"
    __table_args__ = (
        Index("ix_webhook_endpoints_enabled", "enabled"),
        Index("ix_webhook_endpoints_status", "status"),
        Index("ix_webhook_endpoints_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    last_delivery_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=WebhookEndpointStatus.ACTIVE.value
    )
    secret_ref: Mapped[str] = mapped_column(String(160), nullable=False)
    signing_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")


class WebhookEventSubscription(Base):
    __tablename__ = "webhook_event_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "webhook_endpoint_id", "event_type", name="uq_webhook_subscription_endpoint_event"
        ),
        Index("ix_webhook_subscriptions_endpoint", "webhook_endpoint_id"),
        Index("ix_webhook_subscriptions_event_type", "event_type"),
        Index("ix_webhook_subscriptions_enabled", "enabled"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    webhook_endpoint_id: Mapped[int] = mapped_column(
        ForeignKey("webhook_endpoints.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(160), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        Index("ix_webhook_deliveries_endpoint", "webhook_endpoint_id"),
        Index("ix_webhook_deliveries_event_type", "event_type"),
        Index("ix_webhook_deliveries_delivery_id", "delivery_id", unique=True),
        Index("ix_webhook_deliveries_status", "status"),
        Index("ix_webhook_deliveries_created_at", "created_at"),
        Index("ix_webhook_deliveries_next_attempt_at", "next_attempt_at"),
        Index("ix_webhook_deliveries_next_retry_at", "next_retry_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    webhook_endpoint_id: Mapped[int] = mapped_column(
        ForeignKey("webhook_endpoints.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(160), nullable=False)
    event_outbox_id: Mapped[int | None] = mapped_column(
        ForeignKey("event_outbox.id"), nullable=True
    )
    delivery_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=WebhookDeliveryStatus.PENDING.value
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    request_headers_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    request_body_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    request_body_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
