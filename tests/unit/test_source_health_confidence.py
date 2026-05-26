from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.news_source import NewsSource
from app.services.news.provider_confidence_service import HealthResult, ProviderConfidenceService


def _db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return Session(engine)


def test_failure_degrades_confidence() -> None:
    db = _db()
    src = NewsSource(name="a", slug="a", kind="rss", rss_url="https://a.com/rss")
    db.add(src)
    db.commit()
    db.refresh(src)
    svc = ProviderConfidenceService()
    before = src.provider_confidence
    for _ in range(6):
        svc.apply_health_result(db, src, HealthResult(success=False, status_code=500, latency_ms=12000, failure_type="HTTP_5XX"))
        db.refresh(src)
    assert src.provider_confidence < before
    assert src.is_degraded is True


def test_success_recovers_gradually() -> None:
    db = _db()
    src = NewsSource(name="b", slug="b", kind="rss", rss_url="https://b.com/rss", provider_confidence=0.3)
    db.add(src)
    db.commit()
    db.refresh(src)
    svc = ProviderConfidenceService()
    for _ in range(30):
        svc.apply_health_result(db, src, HealthResult(success=True, status_code=200, latency_ms=200))
        db.refresh(src)
    assert 0.3 <= src.provider_confidence <= 0.99


def test_snapshot_creation() -> None:
    db = _db()
    src = NewsSource(name="c", slug="c", kind="rss", rss_url="https://c.com/rss")
    db.add(src)
    db.commit()
    db.refresh(src)
    svc = ProviderConfidenceService()
    svc.apply_health_result(db, src, HealthResult(success=True, status_code=200, latency_ms=100))
    snap = svc.build_health_snapshot(db, src, "1h")
    assert snap.snapshot_window == "1h"
