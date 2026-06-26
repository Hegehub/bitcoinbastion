from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.provider_source_health_timeseries import (
    ProviderHealthTimeSeriesSnapshot,
    SourceHealthTimeSeriesSnapshot,
)
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
    Base.metadata.create_all(
        engine,
        tables=[
            ProviderHealthTimeSeriesSnapshot.__table__,
            SourceHealthTimeSeriesSnapshot.__table__,
        ],
    )
    return Session(engine)


def test_provider_snapshot_write_latest_history_and_degraded_query() -> None:
    db = session()
    repo = ProviderSourceHealthTimeSeriesRepository(db)
    service = HealthSnapshotService(repo)
    now = utcnow()

    service.record_provider_snapshot(
        provider_key="mempool_space",
        domain="market",
        status="ok",
        observed_at=now - timedelta(minutes=5),
        health_score=0.99,
        success_count=10,
    )
    degraded = service.record_provider_snapshot(
        provider_key="mempool_space",
        domain="market",
        status="degraded",
        observed_at=now,
        health_score=0.4,
        failure_count=2,
        is_degraded=True,
        degraded_reason="timeout",
    )
    db.commit()

    assert repo.latest_provider_snapshot("mempool_space").id == degraded.id
    history = repo.provider_history("mempool_space", now - timedelta(hours=1), now, limit=10)
    assert [item.status for item in history] == ["degraded", "ok"]
    assert repo.degraded_providers(now - timedelta(hours=1))[0].degraded_reason == "timeout"
    assert repo.health_summary(now - timedelta(hours=1), now)["degraded_provider_count"] == 1


def test_provider_snapshot_outbox_events_are_safe() -> None:
    class FakeOutbox:
        def __init__(self) -> None:
            self.events = []

        def enqueue_event(self, **kwargs):
            self.events.append(kwargs)

    db = session()
    outbox = FakeOutbox()
    service = HealthSnapshotService(ProviderSourceHealthTimeSeriesRepository(db), outbox=outbox)

    service.record_provider_snapshot(
        provider_key="coinbase",
        domain="market",
        status="degraded",
        is_degraded=True,
        metadata_json={"reason_code": "latency"},
    )

    assert [event["event_type"] for event in outbox.events] == [
        "provider.health.snapshot.recorded",
        "provider.health.degraded",
    ]
    assert "secret" not in str(outbox.events).lower()
