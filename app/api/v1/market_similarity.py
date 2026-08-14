from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.access_dependencies import require_scope
from app.api.dependencies import db_session
from app.domain.access.context import AccessContext
from app.domain.access.scopes import MARKET_INTELLIGENCE_READ
from app.schemas.market_similarity import MarketSimilarityReportOut
from app.services.intelligence.market_similarity_read_service import MarketSimilarityReadService

router = APIRouter(prefix="/market/similarity", tags=["market-similarity"])


@router.get(
    "/{event_id}",
    response_model=MarketSimilarityReportOut,
    operation_id="market_similarity_report",
)
def market_similarity_report(
    event_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(db_session),
    _: AccessContext = Depends(require_scope(MARKET_INTELLIGENCE_READ)),
) -> MarketSimilarityReportOut:
    return MarketSimilarityReadService(db).report(event_id, limit=limit)
