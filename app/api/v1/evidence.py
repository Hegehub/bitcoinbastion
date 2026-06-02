from fastapi import APIRouter, Depends
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.services.intelligence.market_memory.evidence import MarketMemoryEvidenceBuilder
from app.services.intelligence.market_memory.safety import MARKET_MEMORY_SAFETY_LIMITATIONS

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/market-memory/{event_id}")
def get_market_memory_evidence(
    event_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        payload = MarketMemoryEvidenceBuilder(db).payload(event_id, limit=limit)
        db.commit()
        return {"data": payload, "limitations": payload["limitations"]}
    except OperationalError:
        return {
            "data": None,
            "limitations": MARKET_MEMORY_SAFETY_LIMITATIONS
            + ["Market memory evidence storage is unavailable."],
        }
