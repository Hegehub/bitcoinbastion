import json
import logging

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models.event_outbox import EventOutbox, EventOutboxStatus
from app.events.publisher import publish_event
from app.services.events.event_bus_service import (
    EventBusPublishError,
    EventBusService,
    EventPublishStatus,
)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[EventOutbox.__table__])
    return Session(engine)


def test_valid_registered_event_is_written_to_outbox() -> None:
    with _session() as db:
        service = EventBusService(db)
        result = service.publish_event(
            "signal.created",
            {"signal_id": 123, "confidence": 0.72, "limitations": ["correlation_not_causation"]},
            aggregate_type="signal",
            aggregate_id=123,
            source="signal_governance",
        )

        row = db.query(EventOutbox).filter_by(event_id=result.event_id).one()
        assert result.status == EventPublishStatus.PUBLISHED_TO_OUTBOX
        assert result.outbox_status == EventOutboxStatus.PENDING.value
        assert row.event_type == "signal.created"
        assert row.aggregate_id == "123"
        assert row.status == EventOutboxStatus.PENDING.value
        assert json.loads(row.payload_json)["signal_id"] == 123
        metadata = json.loads(row.metadata_json)
        assert metadata["source"] == "signal_governance"
        assert metadata["payload_hash"]
        assert metadata["correlation_id"]


def test_invalid_event_type_is_rejected() -> None:
    with _session() as db:
        service = EventBusService(db)
        with pytest.raises(EventBusPublishError):
            service.publish_event("unknown.created", {"id": 1})


def test_trace_and_provider_examples_publish() -> None:
    with _session() as db:
        service = EventBusService(db)
        trace = service.publish_event(
            "trace.report.created",
            {
                "report_id": 55,
                "address": "bc1qexamplepublicaddress000000000000000000000",
                "trace_band": "medium",
                "advisory_only": True,
                "not_legal_verification": True,
                "not_consensus_proof": True,
                "no_custody": True,
            },
            aggregate_type="trace_report",
            aggregate_id=55,
            source="bastion_trace",
        )
        provider = service.publish_event(
            "provider.degraded",
            {"provider_name": "market_provider", "reason": "stale_data", "degraded": True},
            aggregate_type="provider_health",
            aggregate_id="market_provider",
            source="provider_health",
        )

        assert db.query(EventOutbox).filter_by(event_id=trace.event_id).one().domain == "trace"
        assert db.query(EventOutbox).filter_by(event_id=provider.event_id).one().domain == "provider"


def test_idempotency_key_prevents_duplicate_rows() -> None:
    with _session() as db:
        service = EventBusService(db)
        first = service.publish_event(
            "signal.created",
            {"signal_id": 123},
            idempotency_key="signal-123-created",
        )
        second = service.publish_event(
            "signal.created",
            {"signal_id": 123},
            idempotency_key="signal-123-created",
        )

        assert first.status == EventPublishStatus.PUBLISHED_TO_OUTBOX
        assert second.status == EventPublishStatus.DUPLICATE_IGNORED
        assert second.event_id == first.event_id
        assert db.query(EventOutbox).count() == 1


def test_logs_do_not_include_raw_payload(caplog: pytest.LogCaptureFixture) -> None:
    with _session() as db:
        service = EventBusService(db)
        with caplog.at_level(logging.INFO):
            service.publish_event(
                "signal.created",
                {"signal_id": 123, "sensitive_business_value": "do-not-log"},
                aggregate_type="signal",
                aggregate_id=123,
                source="signal_governance",
            )

    log_text = caplog.text
    assert "event_bus_publish" in log_text
    assert "do-not-log" not in log_text
    assert "sensitive_business_value" not in log_text


def test_public_publish_event_function_is_importable_and_uses_session(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[EventOutbox.__table__])
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    monkeypatch.setattr("app.events.publisher.SessionLocal", testing_session)

    result = publish_event("signal.created", {"signal_id": 456}, source="test")

    assert result.status == EventPublishStatus.PUBLISHED_TO_OUTBOX
    with testing_session() as db:
        assert db.query(EventOutbox).count() == 1
