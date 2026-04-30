from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.job_run import JobRun
from app.tasks.observability_tasks import run_recovery_drill


def test_run_recovery_drill_returns_slo_and_drill_execution(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        db.add(JobRun(task_name="signals.generate", status="success"))
        db.commit()

    monkeypatch.setattr("app.tasks.observability_tasks.SessionLocal", lambda: Session(engine))
    out = run_recovery_drill()
    assert "drill_execution" in out
    assert "recovery_slo" in out
    assert isinstance(out["recovery_slo"]["slo_breached"], bool)
