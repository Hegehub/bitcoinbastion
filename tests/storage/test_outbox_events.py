from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import pytest
from pydantic import ValidationError

from app.db.base import Base
from app.db.models.storage_outbox_event import StorageOutboxEvent, StorageOutboxEventStatus
from app.storage.outbox.schemas import StorageOutboxEventCreate


def _event_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_type": "trace.report.created",
        "aggregate_type": "trace_report",
        "aggregate_id": "trace_123",
        "payload_json": {"report_id": "trace_123"},
        "target_stores": ["clickhouse", "websocket"],
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("field", ["event_type", "aggregate_type", "aggregate_id", "target_stores"])
def test_outbox_required_fields_are_validated(field: str) -> None:
    payload = _event_payload()
    payload[field] = [] if field == "target_stores" else ""

    with pytest.raises(ValidationError):
        StorageOutboxEventCreate(**payload)


def test_payload_json_defaults_to_object_and_targets_are_explicit() -> None:
    event = StorageOutboxEventCreate(**_event_payload(payload_json={}))

    assert event.payload_json == {}
    assert event.target_stores == ["clickhouse", "websocket"]


def test_outbox_model_defaults_before_processing() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[StorageOutboxEvent.__table__])
    with Session(engine) as session:
        event = StorageOutboxEvent(
            event_id="evt_defaults",
            event_type="trace.report.created",
            aggregate_type="trace_report",
            aggregate_id="trace_123",
            payload_json={"report_id": "trace_123"},
            metadata_json={},
            target_stores=["clickhouse"],
        )
        session.add(event)
        session.flush()

        assert event.status == StorageOutboxEventStatus.PENDING.value
        assert event.retry_count == 0
        assert event.processed_at is None
        assert event.last_error is None


def test_failed_event_retains_last_error_shape() -> None:
    event = StorageOutboxEvent(
        event_id="evt_failed",
        event_type="trace.report.created",
        aggregate_type="trace_report",
        aggregate_id="trace_123",
        payload_json={},
        metadata_json={},
        target_stores=["clickhouse"],
        status=StorageOutboxEventStatus.FAILED.value,
        last_error="sanitized failure",
    )

    assert event.status == "failed"
    assert event.last_error == "sanitized failure"


def test_outbox_payload_rejects_sensitive_material() -> None:
    with pytest.raises(ValidationError, match="forbidden sensitive material"):
        StorageOutboxEventCreate(
            **_event_payload(payload_json={"operator_note": "raw access token leaked"})
        )


def test_projection_worker_retry_safe_processing_is_deferred_to_prompt_11_plus() -> None:
    pytest.skip("projection worker execution is not implemented in the storage foundation yet")
