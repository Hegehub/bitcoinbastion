from app.db.session import SessionLocal
from app.db.repositories.storage_outbox_repository import StorageOutboxRepository
from app.storage.outbox.service import StorageOutboxService
from app.tasks.celery_app import celery_app


@celery_app.task(name="storage_outbox.release_stale_locks")  # type: ignore[untyped-decorator]
def release_stale_locks(older_than_seconds: int = 900) -> dict[str, int]:
    with SessionLocal() as db:
        service = StorageOutboxService(StorageOutboxRepository(db))
        released = service.release_stale_locks(older_than_seconds=older_than_seconds)
        return {"released": released}


@celery_app.task(name="storage_outbox.dispatch_pending")  # type: ignore[untyped-decorator]
def dispatch_pending(
    limit: int = 100, worker_id: str = "storage-outbox-placeholder"
) -> dict[str, int]:
    """Claim pending events without projecting to external stores yet.

    Prompt 6 intentionally does not implement TimescaleDB, ClickHouse, Qdrant,
    Redis, Object Storage, webhook, WebSocket, SDK, or MCP projectors. Claimed
    events are returned to retry state with an explicit placeholder error so no
    projection appears to have succeeded.
    """
    with SessionLocal() as db:
        service = StorageOutboxService(StorageOutboxRepository(db))
        events = service.claim_batch(worker_id=worker_id, limit=limit)
        for event in events:
            service.record_retryable_failure(
                event.event_id,
                "storage outbox projector dispatch is not implemented in prompt 6",
                delay_seconds=300,
            )
        return {"claimed": len(events), "projected": 0, "requeued": len(events)}
