from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from redis import RedisError

from app.api.dependencies import db_session
from app.core.cache import get_redis_client
from app.core.config import get_settings
from app.schemas.health import HealthOut

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthOut)
def health() -> HealthOut:
    settings = get_settings()
    return HealthOut(status="ok", app=settings.app_name, details={"mode": "baseline"})


@router.get("/live", response_model=HealthOut)
def liveness() -> HealthOut:
    settings = get_settings()
    return HealthOut(status="live", app=settings.app_name, details={"process": "up"})


@router.get("/ready", response_model=HealthOut)
def readiness(db: Session = Depends(db_session)) -> HealthOut:
    db.execute(text("SELECT 1"))

    redis_status = "ok"
    try:
        get_redis_client().ping()
    except RedisError:
        redis_status = "degraded"

    settings = get_settings()
    status = "ready" if redis_status == "ok" else "degraded"
    return HealthOut(status=status, app=settings.app_name, details={"db": "ok", "redis": redis_status})
