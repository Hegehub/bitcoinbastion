from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, get_admin_user
from app.db.models.auth import User
from app.db.repositories.job_run_repository import JobRunRepository
from app.schemas.admin import JobRunOut
from app.schemas.base import ResponseEnvelope
from app.tasks.celery_app import celery_app

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status", response_model=ResponseEnvelope[dict[str, str]])
def admin_status(_: User = Depends(get_admin_user)) -> ResponseEnvelope[dict[str, str]]:
    return ResponseEnvelope(data={"status": "ok", "module": "admin"})


@router.get("/jobs", response_model=ResponseEnvelope[list[str]])
def admin_jobs(_: User = Depends(get_admin_user)) -> ResponseEnvelope[list[str]]:
    names = sorted(name for name in celery_app.tasks.keys() if not name.startswith("celery."))
    return ResponseEnvelope(data=names)


@router.get("/jobs/runs", response_model=ResponseEnvelope[list[JobRunOut]])
def admin_job_runs(
    limit: int = 50,
    _: User = Depends(get_admin_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[JobRunOut]]:
    rows = JobRunRepository(db).list_recent(limit=limit)
    return ResponseEnvelope(data=[JobRunOut.model_validate(r) for r in rows])
