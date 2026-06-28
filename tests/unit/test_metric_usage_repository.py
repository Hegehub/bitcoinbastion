from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.metric_usage_event import MetricUsageEvent
from app.db.models.time_utils import utcnow
from app.services.usage import MetricUsageEventCreate, MetricUsageRepository, MetricUsageService


def session() -> Session:
    engine = create_engine("sqlite://", future=True, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[MetricUsageEvent.__table__])
    return Session(engine)


def test_metric_usage_repository_records_and_queries_usage() -> None:
    db = session()
    service = MetricUsageService(MetricUsageRepository(db))
    now = utcnow()
    service.record_usage_event(
        MetricUsageEventCreate(
            event_type="metric.query",
            decision="allowed",
            source_component="metrics_api",
            recorded_at=now - timedelta(minutes=1),
            metric_group="market",
            metric_name="btc_price",
            credit_cost=3,
            request_count=2,
            pass_lookup_hash="pass_hash_123",
        )
    )
    service.record_usage_event(
        MetricUsageEventCreate(
            event_type="api.denied",
            decision="denied",
            source_component="metrics_api",
            recorded_at=now,
            metric_group="market",
            metric_name="btc_price",
            request_count=1,
            denial_reason="quota_window",
            pass_lookup_hash="pass_hash_123",
        )
    )
    db.commit()

    summary = service.get_usage_summary(now - timedelta(hours=1), now)
    assert summary.total_requests == 3
    assert summary.total_credits == 3
    assert summary.allowed == 2
    assert summary.denied == 1

    by_group = service.get_usage_by_metric_group("market", now - timedelta(hours=1), now)
    assert [event.decision for event in by_group] == ["denied", "allowed"]
    by_subject = service.get_usage_by_subject(
        "pass", "pass_hash_123", now - timedelta(hours=1), now
    )
    assert len(by_subject) == 2
    assert service.get_credit_consumption(now - timedelta(hours=1), now, metric_group="market") == 3
    assert service.get_denial_summary(now - timedelta(hours=1), now) == {"quota_window": 1}
