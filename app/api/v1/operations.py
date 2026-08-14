from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.access_dependencies import require_plan
from app.api.dependencies import db_session
from app.domain.access.context import AccessContext
from app.domain.access.plans import PlanCode
from app.schemas.health import BackgroundJobHealthOut, HealthOut, ProviderHealthSnapshotOut
from app.schemas.operations import (
    OperationalHealthOut,
    OperationsDrillOut,
    OperationsMetricsSummaryOut,
    OperationsRunbookOut,
    OperationsStatusOut,
)
from app.services.observability.operational_health_service import OperationalHealthService
from app.services.observability.operations_control_service import OperationsControlService
from app.services.observability.operations_reliability_service import (
    OperationsIncidentService,
    OperationsSLOPolicy,
    OperationsSLOService,
)
from app.schemas.operations_reliability import IncidentDetailOut, IncidentOut, OperationsSLOOut
from app.core.config import get_settings

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/status", response_model=OperationsStatusOut)
def status(
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> OperationsStatusOut:
    return OperationsControlService().status(db)


@router.get("/providers", response_model=list[ProviderHealthSnapshotOut])
def providers(
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> list[ProviderHealthSnapshotOut]:
    return OperationsControlService().providers(db)


@router.get("/drills", response_model=list[OperationsDrillOut])
def drills(
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> list[OperationsDrillOut]:
    return OperationsControlService().drills(db)


@router.get("/metrics-summary", response_model=OperationsMetricsSummaryOut)
def metrics_summary(
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> OperationsMetricsSummaryOut:
    return OperationsControlService().metrics_summary(db)


@router.get("/runbooks", response_model=list[OperationsRunbookOut])
def runbooks() -> list[OperationsRunbookOut]:
    return OperationsControlService().runbooks()


@router.get("/health", response_model=OperationalHealthOut)
def health(
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> OperationalHealthOut:
    return OperationalHealthService().health(db)


@router.get("/jobs", response_model=list[BackgroundJobHealthOut])
def jobs(
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> list[BackgroundJobHealthOut]:
    return OperationalHealthService().jobs(db)


@router.get("/metrics", response_model=OperationsMetricsSummaryOut)
def metrics(
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> OperationsMetricsSummaryOut:
    return OperationalHealthService().metrics(db)


@router.get("/readiness", response_model=HealthOut)
def readiness(db: Session = Depends(db_session)) -> HealthOut:
    return OperationalHealthService().readiness(db)


@router.get("/liveness", response_model=HealthOut)
def liveness(db: Session = Depends(db_session)) -> HealthOut:
    return OperationalHealthService().liveness(db)


@router.get(
    "/incidents", response_model=list[IncidentOut], operation_id="operations_list_incidents"
)
def incidents(
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> list[IncidentOut]:
    return OperationsIncidentService().list(db)


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentDetailOut,
    operation_id="operations_get_incident",
)
def incident_detail(
    incident_id: str,
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> IncidentDetailOut:
    result = OperationsIncidentService().detail(db, incident_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return result


@router.get("/slo", response_model=list[OperationsSLOOut], operation_id="operations_list_slo")
def operations_slo(
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> list[OperationsSLOOut]:
    settings = get_settings()
    policies = (
        ()
        if not settings.operations_job_success_slo_enabled
        else (
            OperationsSLOPolicy(
                target=settings.operations_job_success_slo_target,
                window=timedelta(hours=settings.operations_job_success_slo_window_hours),
            ),
        )
    )
    return OperationsSLOService(policies).list(db)
