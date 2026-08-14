import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import db_session
from app.db.models import bastion_trace
from app.db.models.bastion_trace import TraceReport
from app.db.models.event_outbox import EventOutbox
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    bastion_trace.Base.metadata.create_all(
        engine,
        tables=[
            TraceReport.__table__,
            bastion_trace.TraceSource.__table__,
            EventOutbox.__table__,
        ],
    )
    factory = sessionmaker(bind=engine, class_=Session)

    def override_db():
        with factory() as db:
            yield db

    app.dependency_overrides[db_session] = override_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(db_session, None)


PAYLOAD = {
    "subject_type": "BITCOIN_ADDRESS",
    "subject": "1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
    "network": "bitcoin-mainnet",
}


def test_submit_is_typed_synchronous_and_idempotent(client: TestClient) -> None:
    headers = {"Idempotency-Key": "trace-submit-attempt-0001"}
    first = client.post("/api/v1/trace/submit", json=PAYLOAD, headers=headers)
    second = client.post("/api/v1/trace/submit", json=PAYLOAD, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["data"]["report_id"] == second.json()["data"]["report_id"]
    assert first.json()["data"]["idempotency_replayed"] is False
    assert second.json()["data"]["idempotency_replayed"] is True


def test_submit_requires_valid_idempotency_and_server_validates_subject(client: TestClient) -> None:
    assert client.post("/api/v1/trace/submit", json=PAYLOAD).status_code == 422
    invalid = {**PAYLOAD, "subject": "not-an-address"}
    response = client.post(
        "/api/v1/trace/submit",
        json=invalid,
        headers={"Idempotency-Key": "trace-submit-attempt-0002"},
    )
    assert response.status_code == 422
    assert "not-an-address" not in response.text


def test_idempotency_key_cannot_be_reused_for_different_request(client: TestClient) -> None:
    headers = {"Idempotency-Key": "trace-submit-attempt-0003"}
    assert client.post("/api/v1/trace/submit", json=PAYLOAD, headers=headers).status_code == 201
    conflict = {**PAYLOAD, "subject": "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"}
    assert client.post("/api/v1/trace/submit", json=conflict, headers=headers).status_code == 409


def test_report_is_strict_and_reconstructs_from_backend_identity(client: TestClient) -> None:
    created = client.post(
        "/api/v1/trace/submit",
        json=PAYLOAD,
        headers={"Idempotency-Key": "trace-submit-attempt-0004"},
    ).json()["data"]
    response = client.get(f"/api/v1/trace/report/{created['report_id']}")
    assert response.status_code == 200
    report = response.json()["data"]
    assert report["id"] == created["report_id"]
    assert report["address"] == PAYLOAD["subject"]
    assert report["status"] == "COMPLETE"
    assert report["summary"] == "Baseline deterministic scoring report."
