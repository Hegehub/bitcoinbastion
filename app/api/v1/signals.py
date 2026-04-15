from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.signal_repository import SignalRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.recommendation import SignalRecommendationOut
from app.schemas.signal import SignalExplanationOut, SignalOut
from app.services.agentic.recommendation_service import SignalRecommendationService
from app.services.explainability.signal_explainability_service import SignalExplainabilityService

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/top", response_model=ResponseEnvelope[PaginatedData[SignalOut]])
def top_signals(
    limit: int = 10,
    offset: int = 0,
    horizon: str | None = None,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[SignalOut]]:
    repo = SignalRepository(db)
    items = [SignalOut.from_model_with_horizons(item) for item in repo.top(limit=limit, offset=offset, horizon=horizon)]
    return ResponseEnvelope(data=PaginatedData(items=items, total=repo.count(), limit=limit, offset=offset))


@router.get("/{signal_id}/recommendations", response_model=ResponseEnvelope[SignalRecommendationOut])
def signal_recommendations(
    signal_id: int,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[SignalRecommendationOut]:
    repo = SignalRepository(db)
    signal = repo.get(signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    data = SignalRecommendationService().build(signal=signal, evidence_nodes=repo.list_nodes(signal_id))
    return ResponseEnvelope(data=data)


@router.get("/{signal_id}/explanation", response_model=ResponseEnvelope[SignalExplanationOut])
def signal_explanation(
    signal_id: int,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[SignalExplanationOut]:
    data = SignalExplainabilityService().get_explanation(db=db, signal_id=signal_id)
    return ResponseEnvelope(data=data)
