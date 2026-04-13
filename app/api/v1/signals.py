from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.signal_repository import SignalRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.signal import SignalOut

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/top", response_model=ResponseEnvelope[PaginatedData[SignalOut]])
def top_signals(
    limit: int = 10, offset: int = 0, db: Session = Depends(db_session)
) -> ResponseEnvelope[PaginatedData[SignalOut]]:
    repo = SignalRepository(db)
    items = [SignalOut.model_validate(item) for item in repo.top(limit=limit, offset=offset)]
    return ResponseEnvelope(data=PaginatedData(items=items, total=repo.count(), limit=limit, offset=offset))
