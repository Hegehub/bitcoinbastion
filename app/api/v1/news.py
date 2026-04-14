from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.news_repository import NewsRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.news import NewsArticleOut, SourceReputationProfileOut
from app.services.reputation.source_reputation_service import SourceReputationService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/latest", response_model=ResponseEnvelope[PaginatedData[NewsArticleOut]])
def latest_news(
    limit: int = 20, offset: int = 0, db: Session = Depends(db_session)
) -> ResponseEnvelope[PaginatedData[NewsArticleOut]]:
    repo = NewsRepository(db)
    items = [NewsArticleOut.model_validate(item) for item in repo.latest(limit=limit, offset=offset)]
    return ResponseEnvelope(data=PaginatedData(items=items, total=repo.count(), limit=limit, offset=offset))


@router.post("/sources/reputation/refresh", response_model=ResponseEnvelope[list[SourceReputationProfileOut]])
def refresh_source_reputation(db: Session = Depends(db_session)) -> ResponseEnvelope[list[SourceReputationProfileOut]]:
    data = SourceReputationService().refresh_profiles(db=db)
    return ResponseEnvelope(data=data)


@router.get("/sources/reputation", response_model=ResponseEnvelope[list[SourceReputationProfileOut]])
def list_source_reputation(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[SourceReputationProfileOut]]:
    data = SourceReputationService().list_profiles(db=db, limit=limit, offset=offset)
    return ResponseEnvelope(data=data)
