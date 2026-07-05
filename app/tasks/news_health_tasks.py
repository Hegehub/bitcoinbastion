from typing import Any

from celery import shared_task
from sqlalchemy import select

from app.db.models.news import NewsSource
from app.db.session import SessionLocal
from app.services.news.provider_confidence_service import ProviderConfidenceService
from app.services.news.source_health_service import SourceHealthService


@shared_task(name="news.check_source_health", bind=True)  # type: ignore[untyped-decorator]
def check_source_health(self: Any, source_id: int) -> dict[str, str]:
    with SessionLocal() as db:
        source = db.execute(
            select(NewsSource).where(NewsSource.id == source_id)
        ).scalar_one_or_none()
        if source is None:
            return {"status": "not_found"}
        SourceHealthService().check_source(db, source)
        return {"status": "ok"}


@shared_task(name="news.refresh_provider_confidence", bind=True)  # type: ignore[untyped-decorator]
def refresh_provider_confidence(self: Any) -> dict[str, int]:
    with SessionLocal() as db:
        svc = ProviderConfidenceService()
        sources = list(db.execute(select(NewsSource)).scalars())
        for s in sources:
            before = s.provider_confidence
            s.provider_confidence = svc.calculate_provider_confidence(s)
            svc.record_confidence_event(
                db, s.id, "refresh", before, s.provider_confidence, "periodic_refresh", {}
            )
        db.commit()
        return {"updated": len(sources)}


@shared_task(name="news.build_source_health_snapshots", bind=True)  # type: ignore[untyped-decorator]
def build_source_health_snapshots(self: Any) -> dict[str, int]:
    with SessionLocal() as db:
        svc = ProviderConfidenceService()
        sources = list(db.execute(select(NewsSource)).scalars())
        count = 0
        for s in sources:
            for w in ("1h", "24h", "7d"):
                svc.build_health_snapshot(db, s, w)
                count += 1
        return {"snapshots": count}
