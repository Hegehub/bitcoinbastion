from app.db.repositories.job_run_repository import JobRunRepository
from app.db.session import SessionLocal
from app.services.admin.job_service import JobTrackingService
from app.tasks.celery_app import celery_app


@celery_app.task(name="signals.generate", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def generate_signals_task() -> dict[str, int]:
    with SessionLocal() as db:
        with JobTrackingService(JobRunRepository(db)).track("signals.generate"):
            return {"generated": 0}
