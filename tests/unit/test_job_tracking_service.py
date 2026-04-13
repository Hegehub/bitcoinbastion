from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.repositories.job_run_repository import JobRunRepository
from app.services.admin.job_service import JobTrackingService


def test_job_tracking_records_success() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        service = JobTrackingService(JobRunRepository(db))
        with service.track("test.task"):
            pass
        runs = service.list_recent(limit=1)
        assert runs[0].task_name == "test.task"
        assert runs[0].status == "success"
