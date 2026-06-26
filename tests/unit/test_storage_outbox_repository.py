from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.storage_outbox_event import StorageOutboxEvent
from app.db.models.time_utils import utcnow
from app.db.repositories.storage_outbox_repository import StorageOutboxRepository
from app.storage.outbox.enums import StorageOutboxEventStatus


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[StorageOutboxEvent.__table__])
    return Session(engine)


def _event(
    event_id: str, priority: int = 100, available_offset_seconds: int = 0
) -> StorageOutboxEvent:
    return StorageOutboxEvent(
        event_id=event_id,
        event_type="trace.report.created",
        aggregate_type="trace_report",
        aggregate_id=event_id,
        payload_json={"report_id": event_id},
        metadata_json={"source": "test"},
        target_stores=["clickhouse", "websocket"],
        idempotency_key=f"idem:{event_id}",
        priority=priority,
        max_retries=2,
        available_at=utcnow() + timedelta(seconds=available_offset_seconds),
    )


def test_create_outbox_event_and_idempotency_key() -> None:
    with _session() as db:
        repo = StorageOutboxRepository(db)
        first = repo.create_event(_event("event-1"))
        duplicate_event = _event("event-duplicate")
        duplicate_event.idempotency_key = "idem:event-1"
        duplicate = repo.create_event(duplicate_event)

        assert first.id == duplicate.id
        assert repo.get_by_event_id(first.event_id).id == first.id
        assert repo.get_by_idempotency_key("idem:event-1").id == first.id


def test_claim_pending_events_respects_available_at_and_priority() -> None:
    with _session() as db:
        repo = StorageOutboxRepository(db)
        repo.create_event(_event("low", priority=100))
        high = repo.create_event(_event("high", priority=1))
        repo.create_event(_event("future", priority=0, available_offset_seconds=3600))

        claimed = repo.claim_pending_events(worker_id="worker-1", limit=10)

        assert [event.event_id for event in claimed] == [high.event_id, "low"]
        assert all(event.status == StorageOutboxEventStatus.PROCESSING.value for event in claimed)
        assert all(event.locked_by == "worker-1" for event in claimed)


def test_mark_processed_retry_failed_dead_letter_and_counts() -> None:
    with _session() as db:
        repo = StorageOutboxRepository(db)
        event = repo.create_event(_event("event-1"))

        claimed = repo.claim_pending_events(worker_id="worker-1", limit=1)[0]
        retry = repo.mark_retry(
            claimed.event_id, "temporary unavailable", utcnow() + timedelta(seconds=30)
        )
        assert retry.status == StorageOutboxEventStatus.RETRY.value
        assert retry.retry_count == 1
        assert retry.available_at is not None
        assert retry.locked_by is None

        claimed_again = repo.claim_pending_events(worker_id="worker-2", limit=1)
        assert claimed_again == []

        processed = repo.mark_processed(event.event_id)
        assert processed.status == StorageOutboxEventStatus.PROCESSED.value
        assert processed.processed_at is not None

        failed = repo.create_event(_event("event-failed"))
        repo.mark_failed(failed.event_id, "private key leaked in upstream error")
        assert repo.get_by_event_id(failed.event_id).last_error == "[REDACTED]"

        dead = repo.create_event(_event("event-dead"))
        repo.mark_dead_letter(dead.event_id, "permanent projection failure")
        counts = repo.count_by_status()
        assert counts[StorageOutboxEventStatus.PROCESSED.value] == 1
        assert counts[StorageOutboxEventStatus.FAILED.value] == 1
        assert counts[StorageOutboxEventStatus.DEAD_LETTER.value] == 1


def test_release_stale_locks() -> None:
    with _session() as db:
        repo = StorageOutboxRepository(db)
        event = repo.create_event(_event("event-1"))
        repo.claim_pending_events(worker_id="worker-1", limit=1)
        event.locked_at = utcnow() - timedelta(hours=2)
        db.commit()

        released = repo.release_stale_locks(older_than=utcnow() - timedelta(hours=1))
        refreshed = repo.get_by_event_id(event.event_id)
        assert released == 1
        assert refreshed.status == StorageOutboxEventStatus.RETRY.value
        assert refreshed.locked_by is None
