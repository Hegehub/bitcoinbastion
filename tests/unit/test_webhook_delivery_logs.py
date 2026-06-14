import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
import app.db.models.event_outbox  # noqa: F401
from app.db.models.webhooks import WebhookEndpoint
from app.services.events.webhook_delivery_log_service import WebhookDeliveryLogService


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def _endpoint(db: Session) -> WebhookEndpoint:
    endpoint = WebhookEndpoint(
        name="Ops webhook",
        target_url="https://example.com/hooks/bastion",
        secret_ref="webhook_secret_ref:test",
        signing_secret="whsec_test_secret",
    )
    db.add(endpoint)
    db.flush()
    return endpoint


def test_delivery_log_stores_signed_headers_and_body_hash_only() -> None:
    with _session() as db:
        endpoint = _endpoint(db)
        service = WebhookDeliveryLogService(db)
        delivery = service.create_delivery_attempt(
            endpoint=endpoint,
            event_type="webhook.test",
            delivery_id="whd_test",
            raw_body='{"data":{"message":"safe"}}',
            headers={
                "X-Bastion-Event": "webhook.test",
                "X-Bastion-Timestamp": "1780000000",
                "X-Bastion-Delivery-ID": "whd_test",
                "X-Bastion-Signature": "v1=abc",
                "X-Bastion-Payload-Version": "1",
                "X-Bastion-Source": "bitcoin-bastion",
            },
        )

        headers = json.loads(delivery.request_headers_json)
        body_metadata = json.loads(delivery.request_body_json)
        assert headers["X-Bastion-Signature"] == "v1=abc"
        assert delivery.request_body_hash is not None
        assert body_metadata["raw_body_persisted"] is False
        assert "message" not in delivery.request_body_json
        assert "whsec_test_secret" not in delivery.request_headers_json


def test_response_and_error_previews_are_bounded_and_sanitized() -> None:
    with _session() as db:
        endpoint = _endpoint(db)
        service = WebhookDeliveryLogService(db)
        delivery = service.create_delivery_attempt(
            endpoint=endpoint,
            event_type="webhook.test",
            delivery_id="whd_test_2",
            raw_body="{}",
            headers={"X-Bastion-Event": "webhook.test"},
        )

        service.mark_failed(
            delivery,
            error_message="contains private key",
            response_body="x" * 1500,
            response_status_code=500,
            duration_ms=42,
        )

        assert delivery.error_message == "[REDACTED]"
        assert delivery.response_body_preview is not None
        assert len(delivery.response_body_preview) == 1000
        assert delivery.duration_ms == 42
