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


def test_job_tracking_emits_failure_metrics(monkeypatch) -> None:
    calls: dict[str, int] = {"duration": 0, "failure": 0}

    monkeypatch.setattr(
        "app.services.admin.job_service.observe_task_duration",
        lambda **kwargs: calls.__setitem__("duration", calls["duration"] + 1),
    )
    monkeypatch.setattr(
        "app.services.admin.job_service.increment_task_failure",
        lambda **kwargs: calls.__setitem__("failure", calls["failure"] + 1),
    )

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        service = JobTrackingService(JobRunRepository(db))
        try:
            with service.track("test.fail"):
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        runs = service.list_recent(limit=1)

    assert runs[0].status == "failed"
    assert calls["duration"] == 1
    assert calls["failure"] == 1
