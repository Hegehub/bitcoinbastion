from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
import app.db.models.event_outbox  # noqa: F401
from app.db.models.webhooks import (
    WebhookDelivery,
    WebhookDeliveryStatus,
    WebhookEndpoint,
    WebhookEndpointStatus,
    WebhookEventSubscription,
)
from app.db.repositories.webhook_repository import WebhookRepository, WebhookRepositoryError


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def _endpoint() -> WebhookEndpoint:
    return WebhookEndpoint(
        name="Ops webhook",
        target_url="https://example.com/hooks/bastion",
        secret_ref="webhook_secret_ref:test",
    )


def test_create_get_list_and_soft_delete_endpoint() -> None:
    with _session() as db:
        repo = WebhookRepository(db)
        endpoint = repo.create_endpoint(_endpoint())

        assert repo.get_endpoint(endpoint.id).name == "Ops webhook"
        assert repo.list_endpoints()[0].id == endpoint.id

        repo.soft_delete_endpoint(endpoint)
        assert endpoint.enabled is False
        assert endpoint.status == WebhookEndpointStatus.DELETED.value
        assert repo.get_endpoint(endpoint.id) is None
        assert repo.get_endpoint(endpoint.id, include_deleted=True) is not None


def test_create_subscription_and_prevent_duplicates() -> None:
    with _session() as db:
        repo = WebhookRepository(db)
        endpoint = repo.create_endpoint(_endpoint())
        subscription = repo.create_subscription(
            WebhookEventSubscription(webhook_endpoint_id=endpoint.id, event_type="signal.created")
        )

        assert repo.list_subscriptions(endpoint.id)[0].id == subscription.id
        assert repo.get_subscription_by_event(endpoint.id, "signal.created") is not None
        try:
            repo.create_subscription(
                WebhookEventSubscription(
                    webhook_endpoint_id=endpoint.id, event_type="signal.created"
                )
            )
        except WebhookRepositoryError:
            pass
        else:  # pragma: no cover - defensive assertion path
            raise AssertionError("duplicate subscription should fail")


def test_create_and_list_delivery_record() -> None:
    with _session() as db:
        repo = WebhookRepository(db)
        endpoint = repo.create_endpoint(_endpoint())
        delivery = repo.create_delivery(
            WebhookDelivery(
                webhook_endpoint_id=endpoint.id,
                event_type="webhook.test",
                delivery_id="whd_test",
                status=WebhookDeliveryStatus.TEST_CREATED.value,
                target_url=endpoint.target_url,
            )
        )

        rows = repo.list_deliveries(endpoint.id)
        assert rows[0].id == delivery.id
        assert rows[0].status == WebhookDeliveryStatus.TEST_CREATED.value
