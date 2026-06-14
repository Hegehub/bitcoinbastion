from __future__ import annotations

import hashlib
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.time_utils import utcnow
from app.db.models.webhooks import WebhookDelivery, WebhookDeliveryStatus, WebhookEndpoint
from app.db.repositories.webhook_repository import WebhookRepository, WebhookRepositoryError
from app.events.metadata import sanitize_metadata
from app.events.safety import EventPayloadSafetyError, assert_event_payload_safe
from app.events.serializer import serialize_event_json

PREVIEW_LIMIT = 1000


class WebhookDeliveryLogError(ValueError):
    pass


def request_body_hash(raw_body: str) -> str:
    return hashlib.sha256(raw_body.encode("utf-8")).hexdigest()


def sanitize_delivery_preview(value: object, *, limit: int = PREVIEW_LIMIT) -> str | None:
    if value is None:
        return None
    text = str(value)
    try:
        assert_event_payload_safe({"preview": text})
    except EventPayloadSafetyError:
        return "[REDACTED]"
    if len(text) > limit:
        return text[:limit]
    return text


class WebhookDeliveryLogService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = WebhookRepository(db)

    def create_delivery_attempt(
        self,
        *,
        endpoint: WebhookEndpoint,
        event_type: str,
        delivery_id: str,
        raw_body: str,
        headers: dict[str, str],
        event_outbox_id: int | None = None,
        status: str = WebhookDeliveryStatus.PENDING.value,
        attempt_number: int = 1,
        created_at: datetime | None = None,
    ) -> WebhookDelivery:
        safe_headers = sanitize_metadata(headers)
        assert_event_payload_safe(safe_headers)
        body_hash = request_body_hash(raw_body)
        body_metadata: dict[str, object] = {
            "stored": "hash_only",
            "request_body_hash": body_hash,
            "raw_body_persisted": False,
        }
        delivery = WebhookDelivery(
            webhook_endpoint_id=endpoint.id,
            event_type=event_type,
            event_outbox_id=event_outbox_id,
            delivery_id=delivery_id,
            status=status,
            attempt_count=max(attempt_number - 1, 0),
            attempt_number=attempt_number,
            target_url=endpoint.target_url,
            request_headers_json=serialize_event_json(safe_headers),
            request_body_json=serialize_event_json(body_metadata),
            request_body_hash=body_hash,
            created_at=created_at or utcnow(),
        )
        try:
            return self.repository.create_delivery(delivery)
        except WebhookRepositoryError as exc:
            raise WebhookDeliveryLogError(str(exc)) from exc

    def mark_delivered(
        self,
        delivery: WebhookDelivery,
        *,
        response_status_code: int,
        response_body: object | None = None,
        duration_ms: int | None = None,
    ) -> WebhookDelivery:
        delivery.status = WebhookDeliveryStatus.DELIVERED.value
        delivery.response_status_code = response_status_code
        delivery.response_body_preview = sanitize_delivery_preview(response_body)
        delivery.duration_ms = duration_ms
        delivery.delivered_at = utcnow()
        self.repository.update_delivery(delivery)
        return delivery

    def mark_failed(
        self,
        delivery: WebhookDelivery,
        *,
        error_message: object,
        response_status_code: int | None = None,
        response_body: object | None = None,
        duration_ms: int | None = None,
        next_retry_at: datetime | None = None,
    ) -> WebhookDelivery:
        delivery.status = (
            WebhookDeliveryStatus.RETRY_SCHEDULED.value
            if next_retry_at is not None
            else WebhookDeliveryStatus.FAILED.value
        )
        delivery.response_status_code = response_status_code
        delivery.response_body_preview = sanitize_delivery_preview(response_body)
        delivery.error_message = sanitize_delivery_preview(error_message)
        delivery.duration_ms = duration_ms
        delivery.next_retry_at = next_retry_at
        delivery.next_attempt_at = next_retry_at
        self.repository.update_delivery(delivery)
        return delivery
