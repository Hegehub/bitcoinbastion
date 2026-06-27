import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.metric_usage_event import MetricUsageEvent
from app.services.usage import MetricUsageEventCreate, MetricUsageRepository, MetricUsageService


def usage_service() -> MetricUsageService:
    engine = create_engine("sqlite://", future=True, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[MetricUsageEvent.__table__])
    return MetricUsageService(MetricUsageRepository(Session(engine)))


@pytest.mark.parametrize(
    "metadata",
    [
        {"seed_phrase": "never"},
        {"note": "contains private key material"},
        {"nested": {"access_token": "never"}},
    ],
)
def test_metric_usage_rejects_sensitive_metadata(metadata: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        usage_service().record_usage_event(
            MetricUsageEventCreate(
                event_type="api.request",
                decision="allowed",
                source_component="metrics_api",
                metadata_json=metadata,
            )
        )


def test_metric_usage_rejects_raw_subject_identifiers_and_tokenized_urls() -> None:
    with pytest.raises(ValueError):
        usage_service().record_usage_event(
            MetricUsageEventCreate(
                event_type="api.request",
                decision="allowed",
                source_component="metrics_api",
                pass_lookup_hash="alice@example.com",
            )
        )
    with pytest.raises(ValueError):
        usage_service().record_usage_event(
            MetricUsageEventCreate(
                event_type="api.request",
                decision="allowed",
                source_component="metrics_api",
                endpoint="https://internal.example/api?access_token=raw",
            )
        )
