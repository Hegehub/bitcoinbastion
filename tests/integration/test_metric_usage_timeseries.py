from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.metric_usage_event import MetricUsageEvent
from app.db.models.time_utils import utcnow
from app.db.session import get_db
from app.main import app
from app.services.usage import MetricUsageEventCreate, MetricUsageRepository, MetricUsageService


def test_metric_usage_table_and_api_summary_work_without_timescale() -> None:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=[MetricUsageEvent.__table__])
    assert inspect(engine).has_table("metric_usage_events")

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    now = utcnow()
    service = MetricUsageService(MetricUsageRepository(db))
    service.record_usage_event(
        MetricUsageEventCreate(
            event_type="mcp.tool_call",
            decision="allowed",
            source_component="mcp_gateway",
            recorded_at=now - timedelta(minutes=5),
            metric_group="mcp",
            credit_cost=5,
            request_count=1,
        )
    )
    db.commit()
    db.close()

    def override_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    try:
        response = TestClient(app).get("/api/v1/metrics/usage", params={"window_hours": 24})
        assert response.status_code == 200
        payload = response.json()
        assert payload["window"] == "24h"
        assert payload["total_requests"] == 1
        assert payload["total_credits"] == 5
        assert payload["allowed"] == 1
    finally:
        app.dependency_overrides.pop(get_db, None)
