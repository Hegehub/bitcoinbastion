from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.delivery import DeliveryLog
from app.db.models.job_run import JobRun
from app.services.observability.recovery_service import RecoveryCheckService


def test_recovery_check_service_reports_failures_and_actions() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        db.add(JobRun(task_name="ingestion.run", status="failed", error_message="provider timeout"))
        db.add(
            DeliveryLog(
                signal_id=None,
                channel_type="telegram",
                destination="ops-room",
                delivery_status="failed",
                error_message="429 rate limit",
            )
        )
        db.commit()

        out = RecoveryCheckService().evaluate(db=db)

    assert out.ok is False
    assert out.severity == "warning"
    assert out.failed_jobs_24h >= 1
    assert out.failed_deliveries_24h >= 1
    assert out.issues
    assert out.hotspots
    assert out.drills
    assert all(item.automation_ready for item in out.drills)
    assert len(out.recommended_actions) >= 2


def test_recovery_check_service_reports_ok_when_no_failures() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        out = RecoveryCheckService().evaluate(db=db)

    assert out.ok is True
    assert out.severity == "ok"
    assert out.failed_jobs_24h == 0
    assert out.failed_deliveries_24h == 0
    assert out.hotspots == []
    assert out.drills and out.drills[0].drill_code == "routine_recovery_probe"
    assert out.drills[0].run_within_hours == 24
    assert out.recommended_actions == ["No recovery action required. Continue routine observability checks."]


def test_recovery_check_service_reports_critical_when_thresholds_exceed() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        for idx in range(10):
            db.add(JobRun(task_name=f"task-{idx}", status="failed", error_message="boom"))
        db.commit()

        out = RecoveryCheckService().evaluate(db=db)

    assert out.severity == "critical"
    assert out.ok is False


def test_recovery_check_service_adds_drill_action_for_repeated_hotspots() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        for _ in range(3):
            db.add(JobRun(task_name="delivery.publish", status="failed", error_message="timeout"))
        db.add(
            DeliveryLog(
                signal_id=None,
                channel_type="telegram",
                destination="ops-room",
                delivery_status="failed",
                error_message="429 rate limit",
            )
        )
        db.commit()

        out = RecoveryCheckService().evaluate(db=db)

    assert any(item.reference == "delivery.publish" and item.failures_24h == 3 for item in out.hotspots)
    assert any(drill.target_reference == "delivery.publish" and drill.priority == "high" for drill in out.drills)
    assert any(drill.target_reference == "delivery.publish" and drill.run_within_hours == 4 for drill in out.drills)
    assert any("failure-mode drills" in action for action in out.recommended_actions)
