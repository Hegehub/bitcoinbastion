import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
import app.db.models.event_outbox  # noqa: F401
from app.db.models.event_outbox import EventOutboxStatus
from app.db.models.webhooks import WebhookDelivery
from app.db.repositories.event_outbox_repository import EventOutboxRepository
from app.services.events.webhook_dispatcher import WebhookDispatcher


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_dispatcher_blocks_sensitive_payload_without_delivery() -> None:
    with _session() as db:
        event = EventOutboxRepository(db).create_event(
            event_id="evt_sensitive",
            event_type="trace.report.created",
            domain="trace",
            payload_json=json.dumps({"note": "contains private key"}),
            metadata_json="{}",
        )

        result = WebhookDispatcher(db).dispatch_pending_events()
        row = EventOutboxRepository(db).get_by_event_id(event.event_id)

        assert result.blocked == 1
        assert row is not None
        assert row.status == EventOutboxStatus.DEAD_LETTER.value
        assert row.last_error == "[REDACTED]"
        assert db.query(WebhookDelivery).count() == 0
