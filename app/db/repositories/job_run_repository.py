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


    def list_recent_failures(self, limit: int = 20) -> list[JobRun]:
        stmt = (
            select(JobRun)
            .where(JobRun.status.in_(["failed", "error"]))
            .order_by(JobRun.started_at.desc())
            .limit(limit)
        )
        try:
            return list(self.db.execute(stmt).scalars())
        except SQLAlchemyError:
            return []

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

    def top_failed_tasks_last_24h(self, limit: int = 5) -> list[tuple[str, int]]:
        since = datetime.now(UTC) - timedelta(hours=24)
        stmt = (
            select(JobRun.task_name, func.count().label("failure_count"))
            .where(JobRun.started_at >= since)
            .where(JobRun.status.in_(["failed", "error"]))
            .group_by(JobRun.task_name)
            .order_by(func.count().desc(), JobRun.task_name.asc())
            .limit(limit)
        )
        try:
            return [(task_name, int(count)) for task_name, count in self.db.execute(stmt).all()]
        except SQLAlchemyError:
            return []
