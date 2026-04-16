from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, get_admin_user
from app.db.models.auth import User
from app.db.repositories.audit_repository import AuditRepository
from app.db.repositories.job_run_repository import JobRunRepository
from app.schemas.admin import AuditLogOut, JobRetryRequest, JobRetryResponse, JobRunOut, RecoveryCheckOut
from app.schemas.base import ResponseEnvelope
from app.services.observability.recovery_service import RecoveryCheckService
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


@router.get("/audit-logs", response_model=ResponseEnvelope[list[AuditLogOut]])
def admin_audit_logs(
    limit: int = 50,
    action: str | None = None,
    _: User = Depends(get_admin_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[AuditLogOut]]:
    rows = AuditRepository(db).list_recent(limit=limit, action=action)
    return ResponseEnvelope(data=[AuditLogOut.model_validate(r) for r in rows])


@router.post("/jobs/retry", response_model=ResponseEnvelope[JobRetryResponse])
def admin_retry_job(
    payload: JobRetryRequest,
    _: User = Depends(get_admin_user),
) -> ResponseEnvelope[JobRetryResponse]:
    result = celery_app.send_task(payload.task_name)
    return ResponseEnvelope(data=JobRetryResponse(task_name=payload.task_name, task_id=result.id))


@router.get("/jobs/recovery-check", response_model=ResponseEnvelope[RecoveryCheckOut])
def admin_jobs_recovery_check(
    _: User = Depends(get_admin_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[RecoveryCheckOut]:
    data = RecoveryCheckService().evaluate(db=db)
    return ResponseEnvelope(data=data)
