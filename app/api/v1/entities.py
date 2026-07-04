from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.access_dependencies import require_plan, require_scope
from app.api.dependencies import db_session
from app.domain.access.context import AccessContext
from app.domain.access.plans import PlanCode
from app.db.repositories.entity_repository import EntityRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.services.reputation.entity_provenance_service import EntityProvenanceService
from app.schemas.entities import EntityOut, ProvenanceRefreshOut, WatchedEntityOut

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
        EntityOut.from_model(item)
        for item in repo.list_entities(
            limit=limit,
            offset=offset,
            query=q,
            entity_type=entity_type,
            min_confidence=min_confidence,
        )
    ]
    total = repo.count_entities(query=q, entity_type=entity_type, min_confidence=min_confidence)
    return ResponseEnvelope(
        data=PaginatedData(items=items, total=total, limit=limit, offset=offset)
    )


@router.get("/watchlist", response_model=ResponseEnvelope[PaginatedData[WatchedEntityOut]])
def list_watchlist(
    limit: int = 20,
    offset: int = 0,
    access_context: AccessContext = Depends(require_scope("market:intelligence:read")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[WatchedEntityOut]]:
    repo = EntityRepository(db)
    items = [
        WatchedEntityOut.model_validate(item)
        for item in repo.list_watchlist(user_id=_access_actor_id(access_context), limit=limit, offset=offset)
    ]
    total = repo.count_watchlist(user_id=_access_actor_id(access_context))
    return ResponseEnvelope(data=PaginatedData(items=items, total=total, limit=limit, offset=offset))


@router.post("/provenance/refresh", response_model=ResponseEnvelope[ProvenanceRefreshOut])
def refresh_entity_provenance(
    limit: int = 200,
    _: AccessContext = Depends(require_plan(PlanCode.BUSINESS)),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[ProvenanceRefreshOut]:
    data = EntityProvenanceService().refresh(db=db, limit=limit)
    return ResponseEnvelope(data=data)


def _access_actor_id(context: AccessContext) -> int:
    return abs(hash(context.pass_lookup_hash)) % 2_000_000_000
