from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.job_run_repository import JobRunRepository
from app.db.repositories.signal_repository import SignalRepository
from app.db.session import SessionLocal
from app.services.admin.job_service import JobTrackingService
from app.services.delivery.publish_service import SignalPublishService
from app.tasks.celery_app import celery_app




def _should_skip_duplicate_run(*, tracker: JobTrackingService, task_name: str, cooldown_seconds: int = 45) -> bool:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    if not hasattr(tracker, "list_recent"):
        return False
    recent = tracker.list_recent(limit=10)
    for run in recent:
        if run.task_name != task_name:
            continue
        if run.status not in {"started", "success"}:
            continue
        delta = (now - run.started_at).total_seconds()
        if delta <= cooldown_seconds:
            return True
    return False
@celery_app.task(  # type: ignore[untyped-decorator]
    name="delivery.publish",
    autoretry_for=(),
    retry_backoff=False,
    retry_kwargs={"max_retries": 0},
)
def publish_signals_task() -> dict[str, int | str]:
    with SessionLocal() as db:
        tracker = JobTrackingService(JobRunRepository(db))
        if _should_skip_duplicate_run(tracker=tracker, task_name="delivery.publish"):
            return {"status": "skipped", "reason": "duplicate_window_skip"}
        with tracker.track("delivery.publish"):
            published = SignalPublishService(
                signals=SignalRepository(db),
                deliveries=DeliveryRepository(db),
            ).publish_pending_with_stats(limit=30)
            return {
                "published": published.published,
                "failed": published.failed,
                "skipped": published.skipped,
            }
