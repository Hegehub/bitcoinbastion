from typing import Any

from celery import shared_task
from sqlalchemy import select

from app.db.models.news_article import NewsArticle
from app.db.models.news_event import NewsEvent
from app.db.session import SessionLocal
from app.services.intelligence.news_scoring.scoring_service import NewsScoringService


@shared_task(name="news.score_unprocessed", bind=True)  # type: ignore[untyped-decorator]
def score_unprocessed_task(self: Any, limit: int = 100) -> dict[str, int]:
    with SessionLocal() as db:
        rows = list(
            db.execute(select(NewsArticle).order_by(NewsArticle.id.desc()).limit(limit)).scalars()
        )
        svc = NewsScoringService()
        for row in rows:
            svc.score_article(db, row)
        db.commit()
        return {"scored": len(rows)}


@shared_task(name="news.rescore_article", bind=True)  # type: ignore[untyped-decorator]
def rescore_article_task(self: Any, article_id: int) -> dict[str, str]:
    with SessionLocal() as db:
        article = db.get(NewsArticle, article_id)
        if article is None:
            return {"status": "not_found"}
        NewsScoringService().score_article(db, article)
        db.commit()
        return {"status": "ok"}


@shared_task(name="news.rescore_event", bind=True)  # type: ignore[untyped-decorator]
def rescore_event_task(self: Any, event_id: int) -> dict[str, str]:
    with SessionLocal() as db:
        event = db.get(NewsEvent, event_id)
        if event is None:
            return {"status": "not_found"}
        {"status": "skipped"}
        db.commit()
        return {"status": "ok"}
