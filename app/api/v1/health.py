from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from redis import RedisError

from app.api.dependencies import db_session
from app.core.cache import get_redis_client
from app.core.config import get_settings
from app.schemas.health import (
    HealthOut,
    ProviderHealthSnapshotOut,
    RuntimeStatusOut,
    SystemHealthOut,
    BackgroundJobHealthOut,
    DegradedComponentOut,
)
from app.services.observability.runtime_status_service import RuntimeStatusService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthOut)
def health(response: Response, db: Session = Depends(db_session)) -> HealthOut:
    settings = get_settings()
    details: dict[str, str]
    try:
        details = RuntimeStatusService().liveness(db)
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        details = {"process": "up", "db": "unreachable", "migrations": "unknown"}
    state = "ok" if details.get("db") == "ok" else "critical"
    return HealthOut(status=state, app=settings.app_name, details=details)


@router.get("/live", response_model=HealthOut)
def liveness(db: Session = Depends(db_session)) -> HealthOut:
    settings = get_settings()
    details = RuntimeStatusService().liveness(db)
    state = "live" if details.get("db") == "ok" else "critical"
    return HealthOut(status=state, app=settings.app_name, details=details)


@router.get("/ready", response_model=HealthOut)
def readiness(db: Session = Depends(db_session)) -> HealthOut:
    db.execute(text("SELECT 1"))

    redis_status = "ok"
    try:
        get_redis_client().ping()
    except RedisError:
        redis_status = "degraded"

    runtime = RuntimeStatusService().readiness(db)
    settings = get_settings()
    status_value = (
        "ready"
        if redis_status == "ok" and runtime.system_state in {"healthy", "maintenance"}
        else "degraded"
    )
    return HealthOut(
        status=status_value,
        app=settings.app_name,
        details={
            "db": "ok",
            "redis": redis_status,
            "runtime": runtime.system_state,
            "scheduler": runtime.job_state,
            "provider_layer": runtime.provider_state,
        },
    )


@router.get("/providers", response_model=list[ProviderHealthSnapshotOut])
def providers(db: Session = Depends(db_session)) -> list[ProviderHealthSnapshotOut]:
    return RuntimeStatusService().provider_health(db)


@router.get("/jobs", response_model=list[BackgroundJobHealthOut])
def jobs(db: Session = Depends(db_session)) -> list[BackgroundJobHealthOut]:
    return RuntimeStatusService().job_health(db)


@router.get("/runtime", response_model=RuntimeStatusOut)
def runtime(db: Session = Depends(db_session)) -> RuntimeStatusOut:
    return RuntimeStatusService().status(db)


@router.get("/degraded", response_model=list[DegradedComponentOut])
def degraded(db: Session = Depends(db_session)) -> list[DegradedComponentOut]:
    return RuntimeStatusService().status(db).degraded_components


@router.get("/system", response_model=SystemHealthOut)
def system_health(db: Session = Depends(db_session)) -> SystemHealthOut:
    return RuntimeStatusService().system_health(db)
