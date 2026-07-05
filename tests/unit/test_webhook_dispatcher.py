import json

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
import app.db.models.event_outbox  # noqa: F401
from app.db.models.event_outbox import EventOutboxStatus
from app.db.models.webhooks import (
    WebhookDelivery,
    WebhookDeliveryStatus,
    WebhookEndpoint,
    WebhookEndpointStatus,
    WebhookEventSubscription,
)
from app.db.repositories.event_outbox_repository import EventOutboxRepository
from app.services.events.webhook_dispatcher import WebhookDispatcher
from app.services.events.webhook_signature import verify_signature


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def _endpoint(
    db: Session, *, enabled: bool = True, target_url: str = "https://example.com/hook"
) -> WebhookEndpoint:
    endpoint = WebhookEndpoint(
        name="Ops webhook",
        target_url=target_url,
        enabled=enabled,
        status=(
            WebhookEndpointStatus.ACTIVE.value if enabled else WebhookEndpointStatus.DISABLED.value
        ),
        secret_ref="webhook_secret_ref:test",
        signing_secret="whsec_test_secret",
    )
    db.add(endpoint)
    db.flush()
    db.add(WebhookEventSubscription(webhook_endpoint_id=endpoint.id, event_type="signal.created"))
    db.flush()
    return endpoint


def _event(db: Session, *, event_id: str = "evt_signal", attempts: int = 0, max_attempts: int = 8):
    event = EventOutboxRepository(db).create_event(
        event_id=event_id,
        event_type="signal.created",
        domain="signal",
        payload_json=json.dumps(
            {
                "signal_id": 123,
                "limitations": ["informational notification only"],
                "no_custody": True,
                "advisory_only": True,
            }
        ),
        metadata_json="{}",
        max_attempts=max_attempts,
    )
    event.attempts = attempts
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def test_dispatcher_sends_signed_post_to_subscribed_endpoint() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["headers"] = dict(request.headers)
        captured["body"] = request.content.decode()
        return httpx.Response(204, text="ok")

    with _session() as db:
        _endpoint(db)
        event = _event(db)
        dispatcher = WebhookDispatcher(
            db, http_client=httpx.Client(transport=httpx.MockTransport(handler))
        )

        result = dispatcher.dispatch_pending_events()
        row = EventOutboxRepository(db).get_by_event_id(event.event_id)
        delivery = db.query(WebhookDelivery).one()

        assert result.delivered == 1
        assert row is not None
        assert row.status == EventOutboxStatus.DISPATCHED.value
        assert delivery.status == WebhookDeliveryStatus.DELIVERED.value
        assert captured["method"] == "POST"
        headers = captured["headers"]
        assert isinstance(headers, dict)
        assert headers["x-bastion-event"] == "signal.created"
        assert headers["x-bastion-event-id"] == "evt_signal"
        assert headers["x-bastion-signature"].startswith("v1=")
        assert verify_signature(
            secret="whsec_test_secret",
            signature_header=headers["x-bastion-signature"],
            timestamp=int(headers["x-bastion-timestamp"]),
            delivery_id=str(headers["x-bastion-delivery-id"]),
            event_type=str(headers["x-bastion-event"]),
            raw_body=str(captured["body"]),
            now=int(headers["x-bastion-timestamp"]),
        )
        body = json.loads(str(captured["body"]))
        assert body["id"] == "evt_signal"
        assert body["type"] == "signal.created"
        assert body["domain"] == "signal"
        assert body["no_custody"] is True
        assert body["advisory_only"] is True


def test_dispatcher_skips_disabled_endpoint_and_marks_no_subscribers() -> None:
    with _session() as db:
        _endpoint(db, enabled=False)
        event = _event(db, event_id="evt_no_active")

        result = WebhookDispatcher(db).dispatch_pending_events()
        row = EventOutboxRepository(db).get_by_event_id(event.event_id)

        assert result.no_subscribers == 1
        assert row is not None
        assert row.status == EventOutboxStatus.DISPATCHED.value
        assert db.query(WebhookDelivery).count() == 0


def test_dispatcher_marks_no_subscriber_event_safely() -> None:
    with _session() as db:
        event = _event(db, event_id="evt_no_subscribers")

        result = WebhookDispatcher(db).dispatch_pending_events()
        row = EventOutboxRepository(db).get_by_event_id(event.event_id)

        assert result.no_subscribers == 1
        assert row is not None
        assert row.status == EventOutboxStatus.DISPATCHED.value


def test_dispatcher_treats_4xx_as_terminal_delivery_failure() -> None:
    with _session() as db:
        _endpoint(db)
        event = _event(db, event_id="evt_4xx")
        dispatcher = WebhookDispatcher(
            db,
            http_client=httpx.Client(
                transport=httpx.MockTransport(lambda request: httpx.Response(400, text="bad"))
            ),
        )

        result = dispatcher.dispatch_pending_events()
        row = EventOutboxRepository(db).get_by_event_id(event.event_id)
        delivery = db.query(WebhookDelivery).one()

        assert result.delivered == 1
        assert row is not None
        assert row.status == EventOutboxStatus.DISPATCHED.value
        assert delivery.status == WebhookDeliveryStatus.FAILED.value
        assert delivery.response_status_code == 400


def test_dispatcher_retries_5xx_without_faking_success() -> None:
    with _session() as db:
        _endpoint(db)
        event = _event(db, event_id="evt_5xx")
        dispatcher = WebhookDispatcher(
            db,
            http_client=httpx.Client(
                transport=httpx.MockTransport(lambda request: httpx.Response(503, text="down"))
            ),
        )

        result = dispatcher.dispatch_pending_events()
        row = EventOutboxRepository(db).get_by_event_id(event.event_id)
        delivery = db.query(WebhookDelivery).one()

        assert result.retrying == 1
        assert row is not None
        assert row.status == EventOutboxStatus.PENDING.value
        assert row.attempts == 1
        assert row.next_attempt_at is not None
        assert delivery.status == WebhookDeliveryStatus.RETRY_SCHEDULED.value
        assert delivery.next_retry_at is not None


def test_dispatcher_retries_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout")

    with _session() as db:
        _endpoint(db)
        event = _event(db, event_id="evt_timeout")
        dispatcher = WebhookDispatcher(
            db, http_client=httpx.Client(transport=httpx.MockTransport(handler))
        )

        result = dispatcher.dispatch_pending_events()
        row = EventOutboxRepository(db).get_by_event_id(event.event_id)
        delivery = db.query(WebhookDelivery).one()

        assert result.retrying == 1
        assert row is not None
        assert row.status == EventOutboxStatus.PENDING.value
        assert delivery.status == WebhookDeliveryStatus.RETRY_SCHEDULED.value
        assert "timeout" in (delivery.error_message or "")


def test_dispatcher_stops_after_max_attempts() -> None:
    with _session() as db:
        _endpoint(db)
        event = _event(db, event_id="evt_dead", attempts=7, max_attempts=8)
        dispatcher = WebhookDispatcher(
            db,
            http_client=httpx.Client(
                transport=httpx.MockTransport(lambda request: httpx.Response(500, text="down"))
            ),
        )

        result = dispatcher.dispatch_pending_events()
        row = EventOutboxRepository(db).get_by_event_id(event.event_id)

        assert result.dead == 1
        assert row is not None
        assert row.status == EventOutboxStatus.DEAD_LETTER.value
        assert db.query(WebhookDelivery).one().status == WebhookDeliveryStatus.RETRY_SCHEDULED.value


def test_dispatcher_handles_malformed_endpoint_url_safely() -> None:
    with _session() as db:
        _endpoint(db, target_url="not-a-url")
        event = _event(db, event_id="evt_bad_url")

        result = WebhookDispatcher(db).dispatch_pending_events()
        row = EventOutboxRepository(db).get_by_event_id(event.event_id)
        delivery = db.query(WebhookDelivery).one()

        assert result.delivered == 1
        assert row is not None
        assert row.status == EventOutboxStatus.DISPATCHED.value
        assert delivery.status == WebhookDeliveryStatus.FAILED.value
        assert delivery.error_message
        assert "whsec" not in delivery.error_message
