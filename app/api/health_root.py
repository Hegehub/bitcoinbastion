from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.schemas.health import DependencyHealthOut, HealthOut, IntelligenceHealthOut, OperationsHealthOut, ProviderHealthSnapshotOut
from app.services.observability.operations_control_service import OperationsControlService
from app.services.observability.runtime_status_service import RuntimeStatusService

router = APIRouter(prefix="/health", tags=["root-health"])


@router.get("/live", response_model=HealthOut)
def live(db: Session = Depends(db_session)) -> HealthOut:
    details = RuntimeStatusService().liveness(db)
    return HealthOut(status="live" if details.get("db") == "ok" else "critical", app="Bitcoin Bastion", details=details)


@router.get("/ready", response_model=OperationsHealthOut)
def ready(db: Session = Depends(db_session)) -> OperationsHealthOut:
    return OperationsControlService().operations_health(db)


@router.get("/startup", response_model=HealthOut)
def startup(db: Session = Depends(db_session)) -> HealthOut:
    details = RuntimeStatusService().liveness(db)
    startup_status = "started" if details.get("db") == "ok" and details.get("migrations") == "applied" else "degraded"
    return HealthOut(status=startup_status, app="Bitcoin Bastion", details=details)


@router.get("/dependencies", response_model=list[DependencyHealthOut])
def dependencies(db: Session = Depends(db_session)) -> list[DependencyHealthOut]:
    return OperationsControlService().dependencies(db)


@router.get("/providers", response_model=list[ProviderHealthSnapshotOut])
def providers(db: Session = Depends(db_session)) -> list[ProviderHealthSnapshotOut]:
    return OperationsControlService().providers(db)


@router.get("/intelligence", response_model=IntelligenceHealthOut)
def intelligence(db: Session = Depends(db_session)) -> IntelligenceHealthOut:
    return OperationsControlService().intelligence_health(db)


@router.get("/operations", response_model=OperationsHealthOut)
def operations(db: Session = Depends(db_session)) -> OperationsHealthOut:
    return OperationsControlService().operations_health(db)
