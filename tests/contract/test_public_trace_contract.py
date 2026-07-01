import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import db_session
from app.db.models import bastion_trace
from app.main import app


@pytest.fixture(autouse=True)
def trace_db_override():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    trace_tables = [
        bastion_trace.TraceReport.__table__,
        bastion_trace.TraceEvidence.__table__,
        bastion_trace.TraceSource.__table__,
        bastion_trace.TraceSourceSnapshot.__table__,
        bastion_trace.TraceWatchlistEntry.__table__,
        bastion_trace.TraceBatch.__table__,
        bastion_trace.TraceBatchItem.__table__,
        bastion_trace.TraceBusinessPolicyProfileModel.__table__,
        bastion_trace.TraceReviewItem.__table__,
        bastion_trace.TraceOperatorNoteModel.__table__,
        bastion_trace.TraceBusinessProofPacketModel.__table__,
        bastion_trace.TraceBusinessExportModel.__table__,
        bastion_trace.TraceBusinessEventModel.__table__,
    ]
    bastion_trace.Base.metadata.create_all(engine, tables=trace_tables)
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, class_=Session
    )

    def override_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_session] = override_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(db_session, None)


client = TestClient(app)


def test_public_trace_summary_endpoint_uses_response_envelope() -> None:
    created = client.get("/api/v1/trace/address/1BoatSLRHtKNngkdXEeobR76b53LETtpyT")
    assert created.status_code == 200
    report_id = created.json()["data"]["id"]
    response = client.get(f"/api/v1/public/trace/{report_id}/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["report_id"] == report_id
    assert data["limitations"]
    assert data["safety_warnings"]


def test_public_trace_summary_missing_report_returns_404() -> None:
    response = client.get("/api/v1/public/trace/999999999/summary")
    assert response.status_code == 404
