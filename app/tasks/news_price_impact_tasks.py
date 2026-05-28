from typing import Any

from celery import shared_task
from sqlalchemy import select

from app.db.models.news_article import NewsArticle
from app.db.session import SessionLocal
from app.services.intelligence.news_price_impact_service import NewsPriceImpactService


@shared_task(name="news.calculate_price_impact_for_article", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})  # type: ignore[untyped-decorator]
def calculate_price_impact_for_article(self: Any, article_id: int) -> dict[str, str]:
    with SessionLocal() as db:
        row = NewsPriceImpactService().calculate_for_article(db, article_id)
        db.commit()
        return {"status": "ok" if row else "not_found"}


@shared_task(name="news.calculate_price_impact_for_event", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})  # type: ignore[untyped-decorator]
def calculate_price_impact_for_event(self: Any, event_id: int) -> dict[str, str]:
    with SessionLocal() as db:
        row = NewsPriceImpactService().calculate_for_event(db, event_id)
        db.commit()
        return {"status": "ok" if row else "not_found"}


@shared_task(name="news.recalculate_recent_impacts", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 2})  # type: ignore[untyped-decorator]
def recalculate_recent_impacts(self: Any, limit: int = 100) -> dict[str, int]:
    with SessionLocal() as db:
        rows = list(db.execute(select(NewsArticle.id).order_by(NewsArticle.id.desc()).limit(limit)).scalars())
        svc = NewsPriceImpactService()
        done = 0
        for aid in rows:
            if svc.calculate_for_article(db, aid):
                done += 1
        db.commit()
        return {"recalculated": done}
