from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.job_run import JobRun
from app.tasks.observability_tasks import collect_provider_health_snapshots, run_recovery_drill


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


def test_collect_provider_health_snapshots_returns_structured_payload(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("app.tasks.observability_tasks.SessionLocal", lambda: Session(engine))

    out = collect_provider_health_snapshots()
    assert out["status"] == "ok"
    assert isinstance(out["providers"], list)
    assert out["providers"]
    first = out["providers"][0]
    assert "provider_name" in first
    assert "healthy" in first
