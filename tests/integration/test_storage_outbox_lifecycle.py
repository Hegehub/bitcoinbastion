from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.storage_outbox_event import StorageOutboxEvent
from app.db.repositories.storage_outbox_repository import StorageOutboxRepository
from app.storage.outbox.enums import StorageOutboxEventStatus
from app.storage.outbox.service import StorageOutboxService


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[StorageOutboxEvent.__table__])
    return Session(engine)


def test_storage_outbox_lifecycle() -> None:
    with _session() as db:
        service = StorageOutboxService(StorageOutboxRepository(db))
        event = service.enqueue_once(
            idempotency_key="trace.report.created:trace_1",
            event_type="trace.report.created",
            aggregate_type="trace_report",
            aggregate_id="trace_1",
            payload_json={"report_id": "trace_1"},
            target_stores=["clickhouse", "websocket"],
        )

        claimed = service.claim_batch(worker_id="worker-integration", limit=10)
        assert [item.event_id for item in claimed] == [event.event_id]
        assert claimed[0].status == StorageOutboxEventStatus.PROCESSING.value

        processed = service.record_success(event.event_id)
        assert processed.status == StorageOutboxEventStatus.PROCESSED.value
        assert processed.processed_at is not None
        assert service.get_status_counts() == {StorageOutboxEventStatus.PROCESSED.value: 1}
