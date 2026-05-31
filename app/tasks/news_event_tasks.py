from typing import Any

from celery import shared_task
from sqlalchemy import select

from app.db.models.news_event import NewsEvent
from app.db.session import SessionLocal
from app.services.intelligence.event_clustering_service import CanonicalNewsEventService


@shared_task(name="news.cluster_recent_articles", bind=True)  # type: ignore[untyped-decorator]
def cluster_recent_articles_task(self: Any) -> dict[str, int]:
    with SessionLocal() as db:
        count = CanonicalNewsEventService().cluster_recent_articles(db)
        return {"clustered": count}


@shared_task(name="news.rebuild_event", bind=True)  # type: ignore[untyped-decorator]
def rebuild_event_task(self: Any, event_id: int) -> dict[str, str]:
    with SessionLocal() as db:
        event = CanonicalNewsEventService().rebuild_event(db, event_id)
        db.commit()
        return {"status": "ok" if event else "not_found"}


@shared_task(name="news.refresh_event_confidence", bind=True)  # type: ignore[untyped-decorator]
def refresh_event_confidence_task(self: Any) -> dict[str, int]:
    with SessionLocal() as db:
        svc = CanonicalNewsEventService()
        events = list(db.execute(select(NewsEvent).where(NewsEvent.is_active.is_(True))).scalars())
        for event in events:
            event.event_confidence = svc.calculate_event_confidence(db, event)
        db.commit()
        return {"updated": len(events)}
