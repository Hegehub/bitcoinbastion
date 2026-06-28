from app.db.session import SessionLocal
from app.db.repositories.storage_outbox_repository import StorageOutboxRepository
from app.core.config import get_settings
from app.storage.analytics_store.health import build_analytics_store
from app.storage.outbox.service import StorageOutboxService
from app.storage.projections.clickhouse_projector import (
    ClickHouseOutboxProjector,
    project_batch_sync,
)
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


@celery_app.task(name="storage.project_clickhouse_events")  # type: ignore[untyped-decorator]
def project_clickhouse_events(
    batch_size: int = 100,
    event_type: str | None = None,
    max_runtime_seconds: int | None = 30,
    dry_run: bool = False,
) -> dict[str, object]:
    """Project storage outbox events into ClickHouse analytics tables.

    ClickHouse is projection-only. This task returns a disabled summary when
    ClickHouse is not enabled and never makes ClickHouse application truth.
    """

    settings = get_settings()
    if not settings.storage.clickhouse.enabled:
        return {
            "processed": 0,
            "inserted": 0,
            "failed_retryable": 0,
            "failed_terminal": 0,
            "skipped": 0,
            "dry_run": dry_run,
            "clickhouse_enabled": False,
            "reason": "clickhouse_disabled",
            "errors": [],
        }
    with SessionLocal() as db:
        projector = ClickHouseOutboxProjector(
            settings=settings,
            outbox_repository=StorageOutboxRepository(db),
            analytics_store=build_analytics_store(settings),
        )
        return project_batch_sync(
            projector,
            batch_size=batch_size,
            event_type=event_type,
            max_runtime_seconds=max_runtime_seconds,
            dry_run=dry_run,
        ).model_dump()
