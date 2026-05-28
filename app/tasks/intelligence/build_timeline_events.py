from typing import Any
from celery import shared_task
from sqlalchemy import select
from app.db.models.btc_candle import BTCCandle
from app.db.models.news_article import NewsArticle
from app.db.session import SessionLocal
from app.services.intelligence.timeline_normalizer import TimelineNormalizationService
from app.services.intelligence.timeline_service import TimelineService


@shared_task(name="intelligence.build_timeline_events", bind=True)  # type: ignore[untyped-decorator]
def build_timeline_events(self: Any) -> dict[str, int]:
    with SessionLocal() as db:
        norm = TimelineNormalizationService()
        svc = TimelineService()
        payloads = []
        for a in list(db.execute(select(NewsArticle).order_by(NewsArticle.id.desc()).limit(50)).scalars()):
            payloads.append(norm.normalize_news_article(a))
        for c in list(db.execute(select(BTCCandle).order_by(BTCCandle.id.desc()).limit(50)).scalars()):
            payloads.append(norm.normalize_btc_candle(c))
        inserted = svc.bulk_store(db, payloads)
        return {"inserted": inserted}
