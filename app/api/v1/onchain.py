from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.onchain_repository import OnchainRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.onchain import OnchainEventOut

router = APIRouter(prefix="/onchain", tags=["onchain"])


@router.get("/events", response_model=ResponseEnvelope[PaginatedData[OnchainEventOut]])
def onchain_events(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[OnchainEventOut]]:
    repo = OnchainRepository(db)
    items = [OnchainEventOut.model_validate(item) for item in repo.recent(limit=limit, offset=offset)]
    return ResponseEnvelope(data=PaginatedData(items=items, total=repo.count(), limit=limit, offset=offset))
