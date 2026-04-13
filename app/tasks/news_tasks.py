from sqlalchemy import select

from app.db.models.news import NewsSource
from app.db.session import SessionLocal
from app.integrations.rss.client import RSSClient
from app.services.ingestion.news_ingestion import NewsIngestionService
from app.tasks.celery_app import celery_app


@celery_app.task(name="news.fetch")
def fetch_news_task() -> dict[str, int]:
    rss = RSSClient()
    service = NewsIngestionService(rss)
    totals = {"inserted": 0, "duplicates": 0}

    with SessionLocal() as db:
        sources = list(db.execute(select(NewsSource).where(NewsSource.is_active.is_(True))).scalars())
        from app.db.repositories.news_repository import NewsRepository

        repo = NewsRepository(db)
        for source in sources:
            result = service.ingest_source(source, repo)
            totals["inserted"] += result.inserted
            totals["duplicates"] += result.duplicates

    return totals
