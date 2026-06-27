from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import db_session
from app.main import app


def test_timescale_status_endpoint_returns_disabled_structure_without_secrets() -> None:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[db_session] = override_db
    try:
        response = TestClient(app).get("/api/v1/storage/timescale/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["enabled"] is False
        assert payload["continuous_aggregates"]["expected"] >= 17
        assert "secret" not in str(payload).lower()
        assert "postgres://" not in str(payload).lower()
    finally:
        app.dependency_overrides.pop(db_session, None)
