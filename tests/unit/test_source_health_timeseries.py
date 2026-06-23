from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.provider_source_health_timeseries import SourceHealthTimeSeriesSnapshot
from app.db.models.time_utils import utcnow
from app.db.repositories.provider_source_health_timeseries_repository import (
    ProviderSourceHealthTimeSeriesRepository,
)
from app.services.health_timeseries import HealthSnapshotService


def session() -> Session:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=[SourceHealthTimeSeriesSnapshot.__table__])
    return Session(engine)


def test_source_snapshot_write_latest_history_and_degraded_query() -> None:
    db = session()
    repo = ProviderSourceHealthTimeSeriesRepository(db)
    service = HealthSnapshotService(repo)
    now = utcnow()

    service.record_source_snapshot(
        source_key="bitcoin-magazine-rss",
        source_type="rss",
        domain="news",
        status="ok",
        observed_at=now - timedelta(minutes=1),
        success_count=3,
    )
    service.record_source_snapshot(
        source_key="bitcoin-magazine-rss",
        source_type="rss",
        domain="news",
        status="degraded",
        observed_at=now,
        is_degraded=True,
        failure_count=1,
    )
    db.commit()

    assert repo.latest_source_snapshot("bitcoin-magazine-rss").status == "degraded"
    history = repo.source_history("bitcoin-magazine-rss", now - timedelta(hours=1), now, 10)
    assert [item.status for item in history] == ["degraded", "ok"]
    assert len(repo.degraded_sources(now - timedelta(hours=1))) == 1
