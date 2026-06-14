import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
import app.db.models.event_outbox  # noqa: F401
from app.schemas.webhooks import WebhookEndpointCreate, WebhookTestRequest
from app.services.events.event_serializer import build_webhook_event_envelope
from app.services.events.webhook_service import WebhookService, WebhookServiceError


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def _payload() -> WebhookEndpointCreate:
    return WebhookEndpointCreate(
        name="Ops webhook",
        target_url="https://example.com/hooks/bastion",
        event_types=["webhook.test"],
    )


@pytest.mark.parametrize(
    "unsafe",
    [
        "seed phrase",
        "mnemonic",
        "private key",
        "xprv",
        "yprv",
        "zprv",
        "wallet.dat",
        "keystore",
        "12 words",
        "24 words",
        "signing material",
    ],
)
def test_test_payload_rejects_forbidden_sensitive_material(unsafe: str) -> None:
    with _session() as db:
        service = WebhookService(db)
        endpoint = service.create_endpoint(_payload())
        with pytest.raises(WebhookServiceError):
            service.create_test_delivery(endpoint.id, WebhookTestRequest(payload={"note": unsafe}))


def test_webhook_event_envelope_rejects_sensitive_material() -> None:
    with pytest.raises(Exception):
        build_webhook_event_envelope(
            event_id="evt_1",
            event_type="webhook.test",
            data={"nested": {"note": "private key"}},
        )
