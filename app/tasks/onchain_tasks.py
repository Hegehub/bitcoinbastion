from app.core.config import get_settings
from app.db.repositories.job_run_repository import JobRunRepository
from app.db.repositories.onchain_repository import OnchainRepository
from app.db.repositories.signal_repository import SignalRepository
from app.db.session import SessionLocal
from app.integrations.bitcoin.provider import build_bitcoin_provider
from app.services.admin.job_service import JobTrackingService
from app.services.ingestion.onchain_ingestion import OnchainIngestionService
from app.tasks.celery_app import celery_app


@celery_app.task(  # type: ignore[untyped-decorator]
    name="onchain.fetch",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def fetch_onchain_task() -> dict[str, int]:
    settings = get_settings()
    with SessionLocal() as db:
        with JobTrackingService(JobRunRepository(db)).track("onchain.fetch"):
            service = OnchainIngestionService(build_bitcoin_provider(settings), OnchainRepository(db))
            signals = service.ingest_and_generate_signals()
            signal_repo = SignalRepository(db)
            for signal in signals:
                signal_repo.add(signal)
            return {"events": len(signals)}
