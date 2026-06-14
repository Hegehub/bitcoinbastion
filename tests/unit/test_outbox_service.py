import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.event_outbox import EventOutbox, EventOutboxStatus
from app.services.events.outbox_service import EventOutboxService, EventOutboxValidationError


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[EventOutbox.__table__])
    return Session(engine)


def test_record_event_writes_pending_outbox_row() -> None:
    with _session() as db:
        service = EventOutboxService(db)
        item = service.record_event(
            event_type="signal.published",
            domain="signals",
            aggregate_type="signal",
            aggregate_id="123",
            payload={"signal_id": 123, "confidence_band": "moderate"},
            metadata={"source": "signal_governance", "actor_id": "operator-1"},
        )

        assert item.status == EventOutboxStatus.PENDING.value
        assert item.domain == "signal"
        assert item.event_version == 1
        assert json.loads(item.payload_json)["signal_id"] == 123
        assert json.loads(item.metadata_json)["source"] == "signal_governance"


@pytest.mark.parametrize(
    "payload",
    [
        {"note": "seed phrase"},
        {"note": "private key"},
        {"note": "xprv"},
        {"note": "wallet.dat"},
        {"authorization": "Bearer token abc"},
    ],
)
def test_forbidden_payload_material_is_rejected(payload: dict[str, object]) -> None:
    with _session() as db:
        service = EventOutboxService(db)
        with pytest.raises(EventOutboxValidationError):
            service.record_event(event_type="trace.report.created", domain="trace", payload=payload)


def test_secret_like_metadata_is_redacted() -> None:
    with _session() as db:
        service = EventOutboxService(db)
        item = service.record_event(
            event_type="provider.degraded",
            domain="provider_health",
            payload={"provider": "source-a"},
            metadata={
                "authorization": "Bearer token abc",
                "api_key": "secret-value",
                "nested": {"secret_key": "secret-value"},
                "request_id": "req-1",
            },
        )

        metadata = json.loads(item.metadata_json)
        assert metadata["authorization"] == "[REDACTED]"
        assert metadata["api_key"] == "[REDACTED]"
        assert metadata["nested"]["secret_key"] == "[REDACTED]"
        assert metadata["request_id"] == "req-1"


def test_unknown_event_type_and_domain_mismatch_are_rejected() -> None:
    with _session() as db:
        service = EventOutboxService(db)
        with pytest.raises(EventOutboxValidationError):
            service.record_event(event_type="unknown.event.created", domain="system", payload={})
        with pytest.raises(EventOutboxValidationError):
            service.record_event(event_type="trace.report.created", domain="signal", payload={})


def test_oversized_payload_is_rejected_without_persisting() -> None:
    with _session() as db:
        service = EventOutboxService(db)
        with pytest.raises(EventOutboxValidationError):
            service.record_event(
                event_type="signal.created",
                domain="signal",
                payload={"large": "x" * (65 * 1024)},
            )
        assert service.list_pending() == []
