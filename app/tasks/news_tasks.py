from sqlalchemy import select

from app.db.models.news import NewsSource
from app.db.repositories.job_run_repository import JobRunRepository
from app.db.session import SessionLocal
from app.integrations.rss.client import RSSClient
from app.services.admin.job_service import JobTrackingService
from app.services.ingestion.news_ingestion import NewsIngestionService
from app.tasks.celery_app import celery_app


@celery_app.task(
    name="news.fetch",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def fetch_news_task(self) -> dict[str, int]:
    with SessionLocal() as db:
        tracker = JobTrackingService(JobRunRepository(db))
        with tracker.track("news.fetch"):
            rss = RSSClient()
            service = NewsIngestionService(rss)
            totals = {"inserted": 0, "duplicates": 0}

            sources = list(db.execute(select(NewsSource).where(NewsSource.is_active.is_(True))).scalars())
            from app.db.repositories.news_repository import NewsRepository

            repo = NewsRepository(db)
            for source in sources:
                result = service.ingest_source(source, repo)
                totals["inserted"] += result.inserted
                totals["duplicates"] += result.duplicates

            return totals
