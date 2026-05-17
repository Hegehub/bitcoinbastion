from celery import shared_task
from app.db.session import SessionLocal
from app.services.observability.provider_health_service import ProviderHealthService
from app.services.observability.recovery_service import RecoveryCheckService


@shared_task(name="tasks.observability.provider_health")  # type: ignore[untyped-decorator]
def collect_provider_health_snapshots() -> dict[str, object]:
    with SessionLocal() as db:
        snapshots = ProviderHealthService().collect(db=db)
        return {
            "status": "ok",
            "providers": [snapshot.model_dump(mode="json") for snapshot in snapshots],
        }


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
