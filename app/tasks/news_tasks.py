from typing import Any

from celery import shared_task
from sqlalchemy import select

from app.db.models.news import NewsSource
from app.db.session import SessionLocal
from app.services.intelligence.news_ingestion.ingestion_service import IngestionService
from app.services.intelligence.news_ingestion.metrics import NEWS_FETCH_FAILURES_TOTAL
from app.services.intelligence.news_ingestion.rss_client import RSSClient


@shared_task(name="news.fetch_source", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})  # type: ignore[untyped-decorator]
def fetch_source_task(self: Any, source_id: int) -> dict[str, int | str]:
    with SessionLocal() as db:
        source = db.execute(select(NewsSource).where(NewsSource.id == source_id, NewsSource.is_active.is_(True))).scalar_one_or_none()
        if source is None:
            return {"status": "skipped", "reason": "source_not_found"}
        try:
            result = IngestionService(RSSClient()).ingest_source(db, source)
            return {"status": "ok", **result}
        except Exception:
            NEWS_FETCH_FAILURES_TOTAL.labels(source=str(source_id)).inc()
            raise


@shared_task(name="news.fetch_all_sources", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 2})  # type: ignore[untyped-decorator]
def fetch_all_sources_task(self: Any) -> dict[str, int]:
    with SessionLocal() as db:
        sources = list(db.execute(select(NewsSource).where(NewsSource.is_active.is_(True))).scalars())
        total_discovered = 0
        total_inserted = 0
        svc = IngestionService(RSSClient())
        for source in sources:
            result = svc.ingest_source(db, source)
            total_discovered += result["discovered"]
            total_inserted += result["inserted"]
        return {"discovered": total_discovered, "inserted": total_inserted}
