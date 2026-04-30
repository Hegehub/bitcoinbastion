from celery import shared_task
from app.db.session import SessionLocal
from app.services.observability.recovery_service import RecoveryCheckService


@shared_task(name="tasks.observability.provider_health")  # type: ignore[untyped-decorator]
def collect_provider_health_snapshots() -> str:
    return "provider health snapshots collected"


@shared_task(name="tasks.observability.recovery_drill")  # type: ignore[untyped-decorator]
def run_recovery_drill() -> dict[str, object]:
    with SessionLocal() as db:
        snapshot = RecoveryCheckService().evaluate(db=db)
        return {
            "severity": snapshot.severity,
            "ok": snapshot.ok,
            "drill_execution": snapshot.drill_execution,
            "recovery_slo": snapshot.recovery_slo,
        }
