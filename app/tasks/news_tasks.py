from typing import Any, cast

from sqlalchemy import select

from app.db.models.news import NewsSource
from app.db.repositories.job_run_repository import JobRunRepository
from app.db.session import SessionLocal
from app.integrations.rss.client import RSSClient
from app.services.admin.job_service import JobTrackingService
from app.services.ingestion.news_ingestion import NewsIngestionService
from app.tasks.celery_app import celery_app




def _should_skip_duplicate_run(*, tracker: JobTrackingService, task_name: str, cooldown_seconds: int = 45) -> bool:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    if not hasattr(tracker, "list_recent"):
        return False
    recent = tracker.list_recent(limit=10)
    for run in recent:
        if run.task_name != task_name:
            continue
        if run.status not in {"started", "success"}:
            continue
        delta = (now - run.started_at).total_seconds()
        if delta <= cooldown_seconds:
            return True
    return False
@celery_app.task(  # type: ignore[untyped-decorator]
    name="news.fetch",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
    retry_jitter=True,
    retry_backoff_max=120,
)
def fetch_news_task(self: Any) -> dict[str, int | str]:
    with SessionLocal() as db:
        tracker = JobTrackingService(JobRunRepository(db))
        if _should_skip_duplicate_run(tracker=tracker, task_name="news.fetch"):
            return {"status": "skipped", "reason": "duplicate_window_skip"}
        with tracker.track("news.fetch"):
            rss = RSSClient()
            service = NewsIngestionService(rss)
            totals: dict[str, int | str] = {"inserted": 0, "duplicates": 0}

            sources = list(db.execute(select(NewsSource).where(NewsSource.is_active.is_(True))).scalars())
            from app.db.repositories.news_repository import NewsRepository

            repo = NewsRepository(db)
            for source in sources:
                result = service.ingest_source(source, repo)
                totals["inserted"] = cast(int, totals["inserted"]) + result.inserted
                totals["duplicates"] = cast(int, totals["duplicates"]) + result.duplicates

            return totals
