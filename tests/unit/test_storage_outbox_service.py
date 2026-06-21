from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import pytest
from pydantic import ValidationError

from app.db.base import Base
from app.db.models.storage_outbox_event import StorageOutboxEvent
from app.db.repositories.storage_outbox_repository import StorageOutboxRepository
from app.storage.outbox.enums import StorageOutboxEventStatus
from app.storage.outbox.schemas import StorageOutboxEventCreate
from app.storage.outbox.service import StorageOutboxService


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[StorageOutboxEvent.__table__])
    return Session(engine)


def _service(db: Session) -> StorageOutboxService:
    return StorageOutboxService(StorageOutboxRepository(db))


def test_enqueue_event_and_enqueue_once() -> None:
    with _session() as db:
        service = _service(db)
        event = service.enqueue_event(
            event_type="trace.report.created",
            aggregate_type="trace_report",
            aggregate_id="trace_1",
            payload_json={"report_id": "trace_1"},
            target_stores=["clickhouse", "websocket"],
        )
        once = service.enqueue_once(
            idempotency_key="trace_1:create",
            event_type="trace.report.created",
            aggregate_type="trace_report",
            aggregate_id="trace_1",
            payload_json={"report_id": "trace_1"},
            target_stores=["clickhouse"],
        )
        duplicate = service.enqueue_once(
            idempotency_key="trace_1:create",
            event_type="trace.report.created",
            aggregate_type="trace_report",
            aggregate_id="trace_1",
            payload_json={"report_id": "trace_1"},
            target_stores=["clickhouse"],
        )
        assert event.status == StorageOutboxEventStatus.PENDING.value
        assert once.id == duplicate.id


def test_claim_success_retry_and_dead_letter() -> None:
    with _session() as db:
        service = _service(db)
        event = service.enqueue_event(
            event_type="trace.report.created",
            aggregate_type="trace_report",
            aggregate_id="trace_1",
            payload_json={"report_id": "trace_1"},
            target_stores=["clickhouse"],
            max_retries=1,
        )

        claimed = service.claim_batch(worker_id="worker-1", limit=1)
        assert claimed[0].event_id == event.event_id

        retry = service.record_retryable_failure(
            event.event_id, "temporary failure", delay_seconds=60
        )
        assert retry.status == StorageOutboxEventStatus.RETRY.value
        assert retry.retry_count == 1

        dead = service.record_retryable_failure(event.event_id, "temporary failure again")
        assert dead.status == StorageOutboxEventStatus.DEAD_LETTER.value


def test_record_success_and_permanent_failure() -> None:
    with _session() as db:
        service = _service(db)
        success_event = service.enqueue_event(
            event_type="artifact.created",
            aggregate_type="storage_artifact",
            aggregate_id="art_1",
            payload_json={"artifact_id": "art_1"},
            target_stores=["audit"],
        )
        service.claim_batch(worker_id="worker-1", limit=1)
        assert (
            service.record_success(success_event.event_id).status
            == StorageOutboxEventStatus.PROCESSED.value
        )

        failed_event = service.enqueue_event(
            event_type="artifact.failed",
            aggregate_type="storage_artifact",
            aggregate_id="art_2",
            payload_json={"artifact_id": "art_2"},
            target_stores=["audit"],
        )
        assert (
            service.record_permanent_failure(failed_event.event_id, "permanent failure").status
            == StorageOutboxEventStatus.FAILED.value
        )
        assert service.get_status_counts()[StorageOutboxEventStatus.FAILED.value] == 1


def test_payload_validation_rejects_invalid_and_sensitive_events() -> None:
    with pytest.raises(ValidationError):
        StorageOutboxEventCreate(
            event_type="",
            aggregate_type="trace_report",
            aggregate_id="trace_1",
            payload_json={"report_id": "trace_1"},
            target_stores=["clickhouse"],
        )

    with pytest.raises(ValidationError, match="forbidden sensitive material"):
        StorageOutboxEventCreate(
            event_type="trace.report.created",
            aggregate_type="trace_report",
            aggregate_id="trace_1",
            payload_json={"note": "private key export"},
            target_stores=["clickhouse"],
        )

    with pytest.raises(ValidationError):
        StorageOutboxEventCreate(
            event_type="trace.report.created",
            aggregate_type="trace_report",
            aggregate_id="trace_1",
            payload_json={"report_id": "trace_1"},
            target_stores=[],
            max_retries=-1,
        )
