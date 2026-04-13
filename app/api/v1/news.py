from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.news_repository import NewsRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.news import NewsArticleOut

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/latest", response_model=ResponseEnvelope[PaginatedData[NewsArticleOut]])
def latest_news(
    limit: int = 20, offset: int = 0, db: Session = Depends(db_session)
) -> ResponseEnvelope[PaginatedData[NewsArticleOut]]:
    repo = NewsRepository(db)
    items = [NewsArticleOut.model_validate(item) for item in repo.latest(limit=limit, offset=offset)]
    return ResponseEnvelope(data=PaginatedData(items=items, total=repo.count(), limit=limit, offset=offset))
