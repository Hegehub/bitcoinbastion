import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.provider_source_health_timeseries import ProviderHealthTimeSeriesSnapshot
from app.db.repositories.provider_source_health_timeseries_repository import (
    ProviderSourceHealthTimeSeriesRepository,
)
from app.services.health_timeseries import HealthSnapshotService


def test_provider_health_metadata_rejects_sensitive_material() -> None:
    engine = create_engine("sqlite://", future=True, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[ProviderHealthTimeSeriesSnapshot.__table__])
    service = HealthSnapshotService(ProviderSourceHealthTimeSeriesRepository(Session(engine)))

    with pytest.raises(ValueError):
        service.record_provider_snapshot(
            provider_key="safe-provider",
            metadata_json={"api_secret": "do-not-store"},
        )

    with pytest.raises(ValueError):
        service.record_provider_snapshot(
            provider_key="safe-provider",
            metadata_json={"note": "contains private key material"},
        )
