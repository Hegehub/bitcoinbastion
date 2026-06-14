import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.event_outbox import EventOutbox
from app.services.events.event_bus_service import EventBusPublishError, EventBusService


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[EventOutbox.__table__])
    return Session(engine)


@pytest.mark.parametrize(
    "payload",
    [
        {"note": "seed phrase"},
        {"note": "private key"},
        {"note": "xprv"},
        {"note": "wallet.dat"},
        {"nested": [{"note": "recovery phrase"}]},
    ],
)
def test_sensitive_payload_material_is_rejected_before_persistence(
    payload: dict[str, object],
) -> None:
    with _session() as db:
        service = EventBusService(db)
        with pytest.raises(EventBusPublishError):
            service.publish_event("trace.report.created", payload)
        assert db.query(EventOutbox).count() == 0


def test_sensitive_metadata_material_is_rejected_or_redacted_safely() -> None:
    with _session() as db:
        service = EventBusService(db)
        with pytest.raises(EventBusPublishError):
            service.publish_event(
                "signal.created",
                {"signal_id": 123},
                metadata={"operator_note": "contains private key"},
            )

        result = service.publish_event(
            "provider.degraded",
            {"provider_name": "market_provider", "degraded": True},
            metadata={"authorization": "Bearer token abc", "request_id": "req-1"},
        )
        row = db.query(EventOutbox).filter_by(event_id=result.event_id).one()
        metadata = json.loads(row.metadata_json)
        assert metadata["authorization"] == "[REDACTED]"
        assert metadata["request_id"] == "req-1"


def test_unsafe_source_is_rejected() -> None:
    with _session() as db:
        service = EventBusService(db)
        with pytest.raises(EventBusPublishError):
            service.publish_event(
                "signal.created",
                {"signal_id": 1},
                source="authorization bearer token",
            )
