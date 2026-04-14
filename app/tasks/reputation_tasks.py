from celery import shared_task

from app.db.session import SessionLocal
from app.services.reputation.source_reputation_service import SourceReputationService


@shared_task(name="tasks.reputation.refresh")
def refresh_source_reputation() -> str:
    with SessionLocal() as db:
        updated = SourceReputationService().refresh_profiles(db=db)
    return f"source reputation refresh completed: {len(updated)} profiles updated"
