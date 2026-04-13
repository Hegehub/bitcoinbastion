from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.signal_repository import SignalRepository
from app.schemas.signal import SignalOut

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/top", response_model=list[SignalOut])
def top_signals(limit: int = 10, db: Session = Depends(db_session)) -> list[SignalOut]:
    repo = SignalRepository(db)
    return [SignalOut.model_validate(item) for item in repo.top(limit)]
