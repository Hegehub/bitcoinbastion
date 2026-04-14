from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.schemas.base import ResponseEnvelope
from app.schemas.policy import (
    PolicyCatalogOut,
    PolicyCheckRequest,
    PolicyCheckResponse,
    PolicyExecutionLogOut,
)
from app.services.policy.policy_service import TreasuryPolicyService

router = APIRouter(prefix="/policy", tags=["policy"])


@router.post("/check", response_model=ResponseEnvelope[PolicyCheckResponse])
def check_policy(
    payload: PolicyCheckRequest,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PolicyCheckResponse]:
    result = TreasuryPolicyService().evaluate_and_log(db=db, payload=payload)
    return ResponseEnvelope(data=result)


@router.get("/executions", response_model=ResponseEnvelope[list[PolicyExecutionLogOut]])
def list_policy_executions(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[PolicyExecutionLogOut]]:
    data = TreasuryPolicyService().list_executions(db=db, limit=limit, offset=offset)
    return ResponseEnvelope(data=data)


@router.get("/catalog", response_model=ResponseEnvelope[list[PolicyCatalogOut]])
def list_policy_catalog(db: Session = Depends(db_session)) -> ResponseEnvelope[list[PolicyCatalogOut]]:
    data = TreasuryPolicyService().list_catalog(db=db)
    return ResponseEnvelope(data=data)
