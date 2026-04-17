from app.db.repositories.job_run_repository import JobRunRepository
from app.db.session import SessionLocal
from app.services.admin.job_service import JobTrackingService
from app.tasks.celery_app import celery_app


@celery_app.task(name="maintenance.cleanup")  # type: ignore[untyped-decorator]
def cleanup_task() -> dict[str, str]:
    with SessionLocal() as db:
        with JobTrackingService(JobRunRepository(db)).track("maintenance.cleanup"):
            return {"status": "ok"}
