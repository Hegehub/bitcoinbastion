from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import db_session, get_admin_user
from app.db.base import Base
from app.db.models.job_run import JobRun
from app.main import app


class FakeAdmin:
    is_admin = True


def test_admin_job_runs_with_real_schema() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, class_=Session)

    with SessionLocal() as session:
        session.add(JobRun(task_name="news.fetch", status="success", correlation_id="abc"))
        session.commit()

    def override_db():
        with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_admin_user] = lambda: FakeAdmin()
    app.dependency_overrides[db_session] = override_db

    client = TestClient(app)
    try:
        response = client.get("/api/v1/admin/jobs/runs")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["task_name"] == "news.fetch"
    finally:
        app.dependency_overrides.clear()
