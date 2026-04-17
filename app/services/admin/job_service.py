from contextlib import contextmanager
from time import perf_counter
from typing import Iterator
from uuid import uuid4

import structlog

from app.db.models.job_run import JobRun
from app.db.repositories.job_run_repository import JobRunRepository
from app.core.telemetry import increment_task_failure, observe_task_duration


class JobTrackingService:
    def __init__(self, repo: JobRunRepository) -> None:
        self.repo = repo
        self.logger = structlog.get_logger("job_tracking")

    @contextmanager
    def track(self, task_name: str) -> Iterator[JobRun]:
        correlation_id = str(uuid4())
        base_logger = self.logger.bind(
            domain="operations",
            service="job_tracking",
            entity_id=task_name,
            correlation_id=correlation_id,
        )
        started_at = perf_counter()
        run = self.repo.start(task_name=task_name, correlation_id=correlation_id)
        base_logger.info("task_started")
        try:
            yield run
            self.repo.finish(run, status="success")
            duration = perf_counter() - started_at
            observe_task_duration(task_name=task_name, status="success", duration_seconds=duration)
            base_logger.info("task_finished", status="success", duration_seconds=round(duration, 6))
        except Exception as exc:
            self.repo.finish(run, status="failed", error_message=str(exc))
            duration = perf_counter() - started_at
            observe_task_duration(task_name=task_name, status="failed", duration_seconds=duration)
            increment_task_failure(task_name=task_name)
            base_logger.error("task_finished", status="failed", duration_seconds=round(duration, 6), error=str(exc))
            raise

    def list_recent(self, limit: int = 50) -> list[JobRun]:
        return self.repo.list_recent(limit=limit)
