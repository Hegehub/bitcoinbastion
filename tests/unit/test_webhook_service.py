import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
import app.db.models.event_outbox  # noqa: F401
from app.db.models.webhooks import WebhookDeliveryStatus
from app.schemas.webhooks import WebhookEndpointCreate, WebhookEndpointUpdate, WebhookTestRequest
from app.services.events.webhook_service import WebhookService, WebhookServiceError


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def _create_payload() -> WebhookEndpointCreate:
    return WebhookEndpointCreate(
        name="Ops webhook",
        target_url="https://example.com/hooks/bastion",
        description="Operator notification endpoint.",
        event_types=["signal.created", "trace.report.created"],
        metadata={"team": "ops"},
    )


def test_create_endpoint_with_subscriptions() -> None:
    with _session() as db:
        service = WebhookService(db)
        endpoint = service.create_endpoint(_create_payload(), created_by=1)

        assert endpoint.id is not None
        assert endpoint.secret_ref.startswith("webhook_secret_ref:")
        assert endpoint.signing_secret is not None
        assert endpoint.signing_secret.startswith("whsec_")
        assert {row.event_type for row in service.list_subscriptions(endpoint.id)} == {
            "signal.created",
            "trace.report.created",
        }


def test_invalid_event_type_url_and_sensitive_material_are_rejected() -> None:
    with _session() as db:
        service = WebhookService(db)
        with pytest.raises(WebhookServiceError):
            service.create_endpoint(
                _create_payload().model_copy(update={"event_types": ["unknown.created"]})
            )
        with pytest.raises(WebhookServiceError):
            service.create_endpoint(
                _create_payload().model_copy(update={"target_url": "file:///tmp/hook"})
            )
        with pytest.raises(WebhookServiceError):
            service.create_endpoint(
                _create_payload().model_copy(update={"metadata": {"note": "contains seed phrase"}})
            )
        with pytest.raises(WebhookServiceError):
            service.create_endpoint(
                _create_payload().model_copy(update={"target_url": "http://127.0.0.1/hook"})
            )


def test_update_endpoint_and_replace_subscriptions() -> None:
    with _session() as db:
        service = WebhookService(db)
        endpoint = service.create_endpoint(_create_payload())
        updated = service.update_endpoint(
            endpoint.id,
            WebhookEndpointUpdate(
                name="Trace webhook",
                enabled=False,
                event_types=["webhook.test", "provider.degraded"],
                metadata={"team": "trace"},
            ),
        )

        assert updated.name == "Trace webhook"
        assert updated.enabled is False
        assert {row.event_type for row in service.list_subscriptions(endpoint.id)} == {
            "webhook.test",
            "provider.degraded",
        }


def test_test_delivery_record_created_without_network_call() -> None:
    with _session() as db:
        service = WebhookService(db)
        endpoint = service.create_endpoint(_create_payload())
        result = service.create_test_delivery(
            endpoint.id, WebhookTestRequest(payload={"ping": "pong"})
        )
        deliveries = service.list_deliveries(endpoint.id)

        assert result.status == WebhookDeliveryStatus.TEST_CREATED.value
        assert result.event_type == "webhook.test"
        assert result.network_delivery_attempted is False
        assert result.headers["X-Bastion-Event"] == "webhook.test"
        assert result.headers["X-Bastion-Signature"].startswith("v1=")
        assert result.request_body_hash == deliveries[0].request_body_hash
        assert deliveries[0].delivery_id == result.delivery_id
        assert deliveries[0].attempt_count == 0
        assert deliveries[0].attempt_number == 1


def test_disabled_webhook_cannot_create_test_delivery() -> None:
    with _session() as db:
        service = WebhookService(db)
        endpoint = service.create_endpoint(_create_payload())
        service.update_endpoint(endpoint.id, WebhookEndpointUpdate(enabled=False))

        with pytest.raises(WebhookServiceError):
            service.create_test_delivery(endpoint.id, WebhookTestRequest())
