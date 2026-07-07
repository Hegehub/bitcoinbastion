from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.access_dependencies import require_access_session, require_human_intent, require_plan, require_signed_request_for_critical_action
from app.api.dependencies import db_session
from app.domain.access.context import AccessContext
from app.domain.access.plans import PlanCode
from app.schemas.base import ResponseEnvelope
from app.schemas.policy import (
    PolicyCatalogOut,
    PolicyCatalogUpsertIn,
    PolicyCatalogCompareRequest,
    PolicyCatalogCompareOut,
    PolicyCheckRequest,
    PolicyCheckResponse,
    PolicyExecutionLogOut,
    PolicyExecutionSummaryOut,
    PolicySimulationOut,
    PolicySimulationRequest,
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




@router.post("/simulate", response_model=ResponseEnvelope[PolicySimulationOut])
def simulate_policy(
    payload: PolicySimulationRequest,
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PolicySimulationOut]:
    data = TreasuryPolicyService().simulate_compare(db=db, payload=payload)
    return ResponseEnvelope(data=data)


@router.get("/executions", response_model=ResponseEnvelope[list[PolicyExecutionLogOut]])
def list_policy_executions(
    limit: int = 20,
    offset: int = 0,
    _: AccessContext = Depends(require_access_session),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[PolicyExecutionLogOut]]:
    data = TreasuryPolicyService().list_executions(db=db, limit=limit, offset=offset)
    return ResponseEnvelope(data=data)


@router.get("/executions/summary", response_model=ResponseEnvelope[PolicyExecutionSummaryOut])
def policy_execution_summary(
    limit: int = Query(default=200, ge=1, le=1000),
    _: AccessContext = Depends(require_access_session),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PolicyExecutionSummaryOut]:
    data = TreasuryPolicyService().execution_summary(db=db, limit=limit)
    return ResponseEnvelope(data=data)


@router.post("/catalog", response_model=ResponseEnvelope[PolicyCatalogOut])
def upsert_policy_catalog(
    payload: PolicyCatalogUpsertIn,
    _: AccessContext = Depends(require_human_intent("enterprise_policy_change")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PolicyCatalogOut]:
    try:
        data = TreasuryPolicyService().upsert_catalog_entry(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ResponseEnvelope(data=data)




@router.post("/catalog/compare", response_model=ResponseEnvelope[PolicyCatalogCompareOut])
def compare_policy_catalog(
    payload: PolicyCatalogCompareRequest,
    _: AccessContext = Depends(require_signed_request_for_critical_action("enterprise_policy_change")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PolicyCatalogCompareOut]:
    data = TreasuryPolicyService().compare_catalog_profiles(db=db, payload=payload)
    return ResponseEnvelope(data=data)


@router.get("/catalog", response_model=ResponseEnvelope[list[PolicyCatalogOut]])
def list_policy_catalog(
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[PolicyCatalogOut]]:
    data = TreasuryPolicyService().list_catalog(db=db)
    return ResponseEnvelope(data=data)
