from sqlalchemy.orm import Session

from app.db.repositories.news_repository import NewsRepository
from app.db.repositories.job_run_repository import JobRunRepository
from app.db.repositories.onchain_repository import OnchainRepository
from app.db.repositories.signal_repository import SignalRepository
from app.db.session import SessionLocal
from app.services.alerts.signal_engine import SignalEngine
from app.services.admin.job_service import JobTrackingService
from app.tasks.celery_app import celery_app


def generate_signals_for_sources(db: Session, *, limit_per_source: int = 25) -> int:
    signal_repo = SignalRepository(db)
    engine = SignalEngine()
    generated = 0

    for article in NewsRepository(db).latest(limit=limit_per_source):
        source_id = str(article.id)
        if signal_repo.has_source_link(source_type="news_article", source_id=source_id):
            continue
        signal = engine.from_news(
            article,
            explainability={
                "reason": "news_scoring_pipeline",
                "source_type": "news_article",
                "source_id": source_id,
            },
        )
        signal_repo.add_with_source(signal=signal, source_type="news_article", source_id=source_id)
        generated += 1

    for event in OnchainRepository(db).recent(limit=limit_per_source):
        source_id = SignalEngine.onchain_source_id(event)
        if signal_repo.has_source_link(source_type="onchain_event", source_id=source_id):
            continue
        signal = engine.from_onchain_event(event)
        signal_repo.add_with_source(signal=signal, source_type="onchain_event", source_id=source_id)
        generated += 1

    return generated


@celery_app.task(  # type: ignore[untyped-decorator]
    name="signals.generate",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_signals_task() -> dict[str, int]:
    with SessionLocal() as db:
        with JobTrackingService(JobRunRepository(db)).track("signals.generate"):
            generated = generate_signals_for_sources(db)
            return {"generated": generated}
