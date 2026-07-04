from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.access_dependencies import require_plan
from app.api.dependencies import db_session
from app.domain.access.context import AccessContext
from app.domain.access.plans import PlanCode
from app.schemas.health import BackgroundJobHealthOut, HealthOut, ProviderHealthSnapshotOut
from app.schemas.operations import OperationalHealthOut, OperationsDrillOut, OperationsMetricsSummaryOut, OperationsRunbookOut, OperationsStatusOut
from app.services.observability.operational_health_service import OperationalHealthService
from app.services.observability.operations_control_service import OperationsControlService

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
