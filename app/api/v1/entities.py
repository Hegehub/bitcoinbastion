from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, get_current_user
from app.db.models.auth import User
from app.db.repositories.entity_repository import EntityRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.entities import EntityOut, WatchedEntityOut

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("", response_model=ResponseEnvelope[PaginatedData[EntityOut]])
def list_entities(
    limit: int = 20,
    offset: int = 0,
    q: str | None = None,
    entity_type: str | None = None,
    min_confidence: float | None = None,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[EntityOut]]:
    repo = EntityRepository(db)
    items = [
        EntityOut.model_validate(item)
        for item in repo.list_entities(
            limit=limit,
            offset=offset,
            query=q,
            entity_type=entity_type,
            min_confidence=min_confidence,
        )
    ]
    total = repo.count_entities(query=q, entity_type=entity_type, min_confidence=min_confidence)
    return ResponseEnvelope(data=PaginatedData(items=items, total=total, limit=limit, offset=offset))


@router.get("/watchlist", response_model=ResponseEnvelope[PaginatedData[WatchedEntityOut]])
def list_watchlist(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[WatchedEntityOut]]:
    repo = EntityRepository(db)
    items = [
        WatchedEntityOut.model_validate(item)
        for item in repo.list_watchlist(user_id=current_user.id, limit=limit, offset=offset)
    ]
    total = repo.count_watchlist(user_id=current_user.id)
    return ResponseEnvelope(data=PaginatedData(items=items, total=total, limit=limit, offset=offset))
