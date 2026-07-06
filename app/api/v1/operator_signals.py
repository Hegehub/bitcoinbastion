from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.access_dependencies import require_business_role, require_human_intent, require_scope
from app.api.dependencies import db_session
from app.domain.access.context import AccessContext
from app.repositories.intelligence_signal_repository import IntelligenceSignalRepository
from app.schemas.intelligence_operator import OperatorActionRequest
from app.schemas.intelligence_signals import SIGNAL_LIMITATIONS
from app.services.intelligence.operator_review_service import OperatorReviewService
from app.services.intelligence.signal_governance_service import SignalGovernanceService

router = APIRouter(prefix="/operator/signals", tags=["operator-signals"])


@router.get("/pending")
def list_pending_signals(
    access_context: AccessContext = Depends(require_scope("signals:advanced:read")),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    rows = SignalGovernanceService(db).list_public(status="pending_review", limit=100)
    return {"data": rows, "limitations": SIGNAL_LIMITATIONS}


@router.get("/{signal_id}")
def get_operator_signal(
    signal_id: int,
    access_context: AccessContext = Depends(require_scope("signals:advanced:read")),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    payload = SignalGovernanceService(db).get_public(signal_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="signal_candidate_not_found")
    reviews = [OperatorReviewService(db).payload(row) for row in IntelligenceSignalRepository(db).reviews_for(signal_id)]
    return {"data": payload, "reviews": reviews, "limitations": SIGNAL_LIMITATIONS}


@router.post("/{signal_id}/approve")
def approve_signal(
    signal_id: int,
    request: OperatorActionRequest,
    access_context: AccessContext = Depends(require_human_intent("enterprise_policy_change")),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    return _review(db, signal_id, "approved", request)


@router.post("/{signal_id}/reject")
def reject_signal(
    signal_id: int,
    request: OperatorActionRequest,
    access_context: AccessContext = Depends(require_business_role("operator")),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    return _review(db, signal_id, "rejected", request)


@router.post("/{signal_id}/hold")
def hold_signal(
    signal_id: int,
    request: OperatorActionRequest,
    access_context: AccessContext = Depends(require_business_role("operator")),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    return _review(db, signal_id, "held", request)


@router.post("/{signal_id}/needs-more-evidence")
def needs_more_evidence(
    signal_id: int,
    request: OperatorActionRequest,
    access_context: AccessContext = Depends(require_business_role("operator")),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    return _review(db, signal_id, "needs_more_evidence", request)


@router.post("/{signal_id}/mark-false-positive")
def mark_false_positive(
    signal_id: int,
    request: OperatorActionRequest,
    access_context: AccessContext = Depends(require_business_role("operator")),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    return _review(db, signal_id, "false_positive", request, false_positive_marker=True)


@router.post("/{signal_id}/confidence-override")
def confidence_override(
    signal_id: int,
    request: OperatorActionRequest,
    access_context: AccessContext = Depends(require_human_intent("enterprise_policy_change")),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    return _review(db, signal_id, "held", request)


def _review(
    db: Session,
    signal_id: int,
    status: str,
    request: OperatorActionRequest,
    *,
    false_positive_marker: bool = False,
) -> dict[str, object]:
    try:
        row = OperatorReviewService(db).review(
            signal_id,
            status,
            reviewer_id=request.reviewer_id,
            operator_note=request.operator_note,
            decision_reason=request.decision_reason,
            false_positive_marker=false_positive_marker,
            confidence_override=request.confidence_override,
            publish_override=request.publish_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return {"data": OperatorReviewService(db).payload(row), "limitations": SIGNAL_LIMITATIONS}
