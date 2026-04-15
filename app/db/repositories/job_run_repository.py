from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.job_run import JobRun


class JobRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def start(self, task_name: str, correlation_id: str = "") -> JobRun:
        run = JobRun(task_name=task_name, status="started", correlation_id=correlation_id)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def finish(self, run: JobRun, status: str, error_message: str = "") -> JobRun:
        run.status = status
        run.error_message = error_message
        run.finished_at = datetime.now(UTC)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_recent(self, limit: int = 50) -> list[JobRun]:
        stmt = select(JobRun).order_by(JobRun.started_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars())

    def started_count_last_24h(self) -> int:
        since = datetime.now(UTC) - timedelta(hours=24)
        stmt = select(func.count()).select_from(JobRun).where(JobRun.started_at >= since)
        try:
            return int(self.db.execute(stmt).scalar_one())
        except SQLAlchemyError:
            return 0

    def failed_count_last_24h(self) -> int:
        since = datetime.now(UTC) - timedelta(hours=24)
        stmt = (
            select(func.count())
            .select_from(JobRun)
            .where(JobRun.started_at >= since)
            .where(JobRun.status.in_(["failed", "error"]))
        )
        try:
            return int(self.db.execute(stmt).scalar_one())
        except SQLAlchemyError:
            return 0
