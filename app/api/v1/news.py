from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.news_repository import NewsRepository
from app.schemas.news import NewsArticleOut

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/latest", response_model=list[NewsArticleOut])
def latest_news(limit: int = 20, db: Session = Depends(db_session)) -> list[NewsArticleOut]:
    repo = NewsRepository(db)
    return [NewsArticleOut.model_validate(item) for item in repo.latest(limit)]
