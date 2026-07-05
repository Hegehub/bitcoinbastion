from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.repositories.intelligence_signal_repository import IntelligenceSignalRepository
from app.schemas.intelligence_signals import SIGNAL_LIMITATIONS
from app.services.intelligence.signal_governance_service import SignalGovernanceService
from app.services.intelligence.signal_delivery_log_service import SignalDeliveryLogService

router = APIRouter(prefix="/signals", tags=["intelligence-signals"])


@router.get("/news-market-impact")
def news_market_impact_signals(db: Session = Depends(db_session)) -> dict[str, object]:
    return {
        "data": SignalGovernanceService(db).list_public(signal_type="news_market_impact"),
        "limitations": SIGNAL_LIMITATIONS,
    }


@router.get("/latest")
def latest_signals(db: Session = Depends(db_session)) -> dict[str, object]:
    return {
        "data": SignalGovernanceService(db).list_public(limit=50),
        "limitations": SIGNAL_LIMITATIONS,
    }


@router.get("/{signal_id}")
def get_signal(signal_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    payload = SignalGovernanceService(db).get_public(signal_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="signal_candidate_not_found")
    return {"data": payload, "limitations": SIGNAL_LIMITATIONS}


@router.get("/{signal_id}/evidence")
def get_signal_evidence(signal_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    row = IntelligenceSignalRepository(db).get_candidate(signal_id)
    if row is None:
        raise HTTPException(status_code=404, detail="signal_candidate_not_found")
    return {
        "data": SignalGovernanceService(db).evidence_refs(row),
        "limitations": SIGNAL_LIMITATIONS,
    }


@router.get("/{signal_id}/delivery-logs")
def get_signal_delivery_logs(
    signal_id: int, db: Session = Depends(db_session)
) -> dict[str, object]:
    if IntelligenceSignalRepository(db).get_candidate(signal_id) is None:
        raise HTTPException(status_code=404, detail="signal_candidate_not_found")
    service = SignalDeliveryLogService(db)
    rows = IntelligenceSignalRepository(db).delivery_logs_for(signal_id)
    return {"data": [service.payload(row) for row in rows], "limitations": SIGNAL_LIMITATIONS}
