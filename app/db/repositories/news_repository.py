from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.news import NewsArticle


class NewsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_hash(self, content_hash: str) -> NewsArticle | None:
        stmt = select(NewsArticle).where(NewsArticle.content_hash == content_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def add(self, article: NewsArticle) -> NewsArticle:
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article

    def latest(self, limit: int = 20) -> list[NewsArticle]:
        stmt = select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars())
