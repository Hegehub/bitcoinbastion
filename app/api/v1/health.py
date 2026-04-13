from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.core.config import get_settings
from app.schemas.health import HealthOut

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthOut)
def health() -> HealthOut:
    settings = get_settings()
    return HealthOut(status="ok", app=settings.app_name)


@router.get("/live", response_model=HealthOut)
def liveness() -> HealthOut:
    settings = get_settings()
    return HealthOut(status="live", app=settings.app_name)


@router.get("/ready", response_model=HealthOut)
def readiness(db: Session = Depends(db_session)) -> HealthOut:
    db.execute(text("SELECT 1"))
    settings = get_settings()
    return HealthOut(status="ready", app=settings.app_name)
