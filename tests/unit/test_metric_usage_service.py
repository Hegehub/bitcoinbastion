import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.metric_usage_event import MetricUsageEvent
from app.services.usage import MetricUsageEventCreate, MetricUsageRepository, MetricUsageService


def service() -> MetricUsageService:
    engine = create_engine("sqlite://", future=True, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[MetricUsageEvent.__table__])
    return MetricUsageService(MetricUsageRepository(Session(engine)))


def test_metric_usage_service_validates_credit_cost_and_request_count() -> None:
    usage_service = service()
    with pytest.raises(ValueError):
        usage_service.record_usage_event(
            MetricUsageEventCreate(
                event_type="api.request",
                decision="allowed",
                source_component="metrics_api",
                credit_cost=-1,
            )
        )
    with pytest.raises(ValueError):
        usage_service.record_usage_event(
            MetricUsageEventCreate(
                event_type="api.request",
                decision="allowed",
                source_component="metrics_api",
                request_count=0,
            )
        )


def test_metric_usage_service_normalizes_labels_and_emits_safe_outbox() -> None:
    class FakeOutbox:
        def __init__(self) -> None:
            self.events = []

        def enqueue_event(self, **kwargs):
            self.events.append(kwargs)

    engine = create_engine("sqlite://", future=True, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[MetricUsageEvent.__table__])
    outbox = FakeOutbox()
    usage_service = MetricUsageService(MetricUsageRepository(Session(engine)), outbox=outbox)

    event = usage_service.record_usage_event(
        MetricUsageEventCreate(
            event_type="SDK.Request",
            decision="Allowed",
            source_component="SDK Gateway",
            metric_group="Developer SDK",
            metric_name="Trace Summary",
            endpoint="/api/v1/public/trace/{report_id}/summary",
            api_key_hash="api_hash_abc",
        )
    )

    assert event.event_type == "sdk.request"
    assert event.metric_group == "developer_sdk"
    assert outbox.events[0]["event_type"] == "metric.usage.recorded"
    assert "api_hash_abc" not in str(outbox.events)
