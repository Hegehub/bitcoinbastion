from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.provider_source_health_timeseries import (
    ProviderHealthTimeSeriesSnapshot,
    SourceHealthTimeSeriesSnapshot,
)
from app.db.models.time_utils import utcnow
from app.db.session import get_db
from app.main import app
from app.services.health_timeseries import HealthSnapshotService
from app.db.repositories.provider_source_health_timeseries_repository import (
    ProviderSourceHealthTimeSeriesRepository,
)


def test_provider_source_health_history_api_is_bounded_and_secret_safe() -> None:
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
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSessionLocal()
    service = HealthSnapshotService(ProviderSourceHealthTimeSeriesRepository(db))
    now = utcnow()
    service.record_provider_snapshot(
        provider_key="kraken",
        domain="market",
        status="ok",
        observed_at=now - timedelta(minutes=2),
        metadata_json={"safe_note": "public status"},
    )
    service.record_source_snapshot(
        source_key="news-rss",
        domain="news",
        status="degraded",
        observed_at=now - timedelta(minutes=1),
        is_degraded=True,
    )
    db.commit()
    db.close()

    def override_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        provider_response = client.get(
            "/api/v1/metrics/provider-health/history",
            params={"provider_key": "kraken", "limit": 10},
        )
        assert provider_response.status_code == 200
        payload = provider_response.json()
        assert payload["items"][0]["provider_key"] == "kraken"
        assert "metadata_json" not in payload["items"][0]
        assert "secret" not in str(payload).lower()

        source_response = client.get(
            "/api/v1/metrics/source-health/latest",
            params={"source_key": "news-rss"},
        )
        assert source_response.status_code == 200
        assert source_response.json()["is_degraded"] is True

        invalid_response = client.get(
            "/api/v1/metrics/provider-health/history",
            params={"provider_key": "kraken", "limit": 501},
        )
        assert invalid_response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)
