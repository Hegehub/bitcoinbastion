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


def _create_report() -> int:
    response = client.get("/api/v1/trace/address/1BoatSLRHtKNngkdXEeobR76b53LETtpyT")
    assert response.status_code == 200
    return int(response.json()["data"]["id"])


def test_trace_proof_packet_endpoint_is_truthful_unsigned_summary() -> None:
    report_id = _create_report()
    response = client.get(f"/api/v1/trace/report/{report_id}/proof-packet")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["report_id"] == report_id
    assert data["advisory_only"] is True
    assert data["not_legal_verification"] is True
    assert data["not_bitcoin_consensus_proof"] is True
    assert data["no_custody"] is True
    assert data["signed"] is False
    assert data["signature_available"] is False
    assert data["signature_status"] == "unsigned"
    assert data["packet_type"] == "application_level_evidence_summary"
    assert isinstance(data["evidence_refs"], list)
    assert "Proof packet is an application-level evidence summary." in data["limitations"]
    text = str(data).lower()
    for forbidden in [
        "clean address",
        "dirty address",
        "criminal address",
        "guaranteed safe",
        "approved payment",
        "verified illicit",
    ]:
        assert forbidden not in text


def test_trace_proof_packet_missing_report_returns_404() -> None:
    response = client.get("/api/v1/trace/report/999999999/proof-packet")
    assert response.status_code == 404


def test_trace_status_contract_is_public_safe_baseline() -> None:
    response = client.get("/api/v1/trace/status")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "baseline"
    assert data["trace_available"] is True
    assert data["calibration_status"] == "not_production_calibrated"
    assert data["provider_status"] == "baseline_or_degraded_visible"
    assert data["trace_production_calibrated"] is False
    assert "Trace scoring is advisory-only." in data["limitations"]


def test_trace_events_contract_is_runtime_events_not_business_payloads() -> None:
    response = client.get("/api/v1/trace/events")
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    for item in data:
        assert "event_type" in item
        assert "payload" not in item
