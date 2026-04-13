from contextlib import contextmanager
from uuid import uuid4

from app.db.models.job_run import JobRun
from app.db.repositories.job_run_repository import JobRunRepository


class JobTrackingService:
    def __init__(self, repo: JobRunRepository) -> None:
        self.repo = repo

    @contextmanager
    def track(self, task_name: str):
        correlation_id = str(uuid4())
        run = self.repo.start(task_name=task_name, correlation_id=correlation_id)
        try:
            yield run
            self.repo.finish(run, status="success")
        except Exception as exc:
            self.repo.finish(run, status="failed", error_message=str(exc))
            raise

    def list_recent(self, limit: int = 50) -> list[JobRun]:
        return self.repo.list_recent(limit=limit)
