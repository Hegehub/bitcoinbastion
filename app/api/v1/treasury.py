from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.access_dependencies import require_human_intent, require_plan, require_scope
from app.api.dependencies import db_session
from app.domain.access.context import AccessContext
from app.domain.access.plans import PlanCode
from app.db.repositories.treasury_repository import TreasuryRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.treasury import (
    TreasuryApprovalActionIn,
    TreasuryApprovalOut,
    TreasuryRejectActionIn,
    TreasuryRejectOut,
    TreasuryRequestIn,
    TreasuryRequestOut,
)
from app.services.treasury.treasury_service import TreasuryService

router = APIRouter(prefix="/treasury", tags=["treasury"])


@router.post("/requests", response_model=ResponseEnvelope[TreasuryRequestOut])
def create_request(
    payload: TreasuryRequestIn,
    access_context: AccessContext = Depends(require_scope("treasury:read")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[TreasuryRequestOut]:
    service = TreasuryService(TreasuryRepository(db))
    created = service.create_request(payload, requested_by=_access_actor_id(access_context))
    return ResponseEnvelope(data=TreasuryRequestOut.from_model_with_policy(created))


@router.post("/requests/{request_id}/approve", response_model=ResponseEnvelope[TreasuryApprovalOut])
def approve_request(
    request_id: int,
    payload: TreasuryApprovalActionIn,
    access_context: AccessContext = Depends(require_human_intent("treasury_policy_change")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[TreasuryApprovalOut]:
    service = TreasuryService(TreasuryRepository(db))
    try:
        result = service.approve_request(request_id=request_id, approver_user_id=_access_actor_id(access_context), payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResponseEnvelope(data=result)


@router.post("/requests/{request_id}/reject", response_model=ResponseEnvelope[TreasuryRejectOut])
def reject_request(
    request_id: int,
    payload: TreasuryRejectActionIn,
    access_context: AccessContext = Depends(require_human_intent("treasury_policy_change")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[TreasuryRejectOut]:
    service = TreasuryService(TreasuryRepository(db))
    try:
        result = service.reject_request(request_id=request_id, actor_user_id=_access_actor_id(access_context), payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResponseEnvelope(data=result)


@router.get(
    "/requests/pending-approvals",
    response_model=ResponseEnvelope[PaginatedData[TreasuryRequestOut]],
)
def list_pending_approvals(
    limit: int = 20,
    offset: int = 0,
    _: AccessContext = Depends(require_plan(PlanCode.PRO)),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[TreasuryRequestOut]]:
    service = TreasuryService(TreasuryRepository(db))
    items = [
        TreasuryRequestOut.from_model_with_policy(item)
        for item in service.list_pending_approvals(limit=limit, offset=offset)
    ]
    total = service.count_pending_approvals()
    return ResponseEnvelope(
        data=PaginatedData(items=items, total=total, limit=limit, offset=offset)
    )


@router.get("/requests", response_model=ResponseEnvelope[PaginatedData[TreasuryRequestOut]])
def list_requests(
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    _: AccessContext = Depends(require_scope("treasury:read")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[TreasuryRequestOut]]:
    service = TreasuryService(TreasuryRepository(db))
    items = [
        TreasuryRequestOut.from_model_with_policy(item)
        for item in service.list_requests(limit=limit, offset=offset, status=status)
    ]
    total = service.count_requests(status=status)
    return ResponseEnvelope(data=PaginatedData(items=items, total=total, limit=limit, offset=offset))


def _access_actor_id(context: AccessContext) -> int:
    return abs(hash(context.session_id_hash)) % 2_000_000_000
