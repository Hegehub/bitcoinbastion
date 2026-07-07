from datetime import UTC, datetime, timedelta

import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.access import RecoveryAttempt, RecoveryQuorum
from app.db.session import get_db
from app.main import app


def _client() -> tuple[TestClient, sessionmaker[Session]]:
    os.environ["ACCESS_SERVER_PEPPER"] = "test-recovery-pepper"
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)

    def override_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), SessionLocal


def test_recovery_api_lifecycle() -> None:
    client, SessionLocal = _client()
    try:
        setup = client.post(
            "/api/v1/access/recovery/setup",
            json={"pass_lookup_hash": "hmac-sha256:pass", "certificate_fingerprint": "sha256:cert", "plan_code": "pro_pass"},
        )
        assert setup.status_code == 200
        phrase_words = setup.json()["bastion_recovery_phrase"]
        assert len(phrase_words) == 24
        assert "Bitcoin wallet seed" in setup.json()["warning"]
        with SessionLocal() as db:
            quorum = db.execute(select(RecoveryQuorum)).scalar_one()
            assert " ".join(phrase_words) not in str(quorum.factors_json)

        start = client.post(
            "/api/v1/access/recovery/start",
            json={"pass_lookup_hash": "hmac-sha256:pass", "certificate_fingerprint": "sha256:cert", "declared_plan_code": "pro_pass", "new_device_key_fingerprint": "sha256:new-device"},
        )
        assert start.status_code == 200
        attempt_id = start.json()["recovery_attempt_id"]
        assert start.json()["threshold"] == 2

        one_factor = client.post(
            "/api/v1/access/recovery/factors",
            json={"recovery_attempt_id": attempt_id, "factor_type": "recovery_phrase_24", "recovery_factor": " ".join(phrase_words)},
        )
        assert one_factor.status_code == 200
        assert one_factor.json()["decision"] == "quorum_incomplete"

        status = client.get(f"/api/v1/access/recovery/status/{attempt_id}")
        assert status.status_code == 200
        assert status.json()["missing_factor_count"] == 1

        second = client.post(
            "/api/v1/access/recovery/factors",
            json={"recovery_attempt_id": attempt_id, "factor_type": "desktop_vault", "recovery_factor": "desktop_vault-proof"},
        )
        assert second.status_code == 200
        assert second.json()["decision"] == "allow"

        blocked = client.post("/api/v1/access/recovery/complete", json={"recovery_attempt_id": attempt_id})
        assert blocked.status_code == 403
        body = blocked.json()
        code = body.get("error", {}).get("code") or body.get("detail", {}).get("code")
        assert code in {"cooldown_required", "http_error"}

        with SessionLocal() as db:
            attempt = db.execute(select(RecoveryAttempt).where(RecoveryAttempt.attempt_hash == attempt_id)).scalar_one()
            attempt.cooldown_until = datetime.now(UTC) - timedelta(seconds=1)
            db.commit()

        completed = client.post(
            "/api/v1/access/recovery/complete",
            json={"recovery_attempt_id": attempt_id, "new_device_public_key": "pub", "new_device_key_fingerprint": "sha256:new-device"},
        )
        assert completed.status_code == 200
        assert completed.json()["status"] == "completed"
    finally:
        app.dependency_overrides.clear()


def test_recovery_api_rejects_bitcoin_seed_fields_and_values() -> None:
    client, _ = _client()
    try:
        response = client.post(
            "/api/v1/access/recovery/factors",
            json={
                "recovery_attempt_id": "attempt",
                "factor_type": "recovery_phrase_12",
                "recovery_factor": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
                "bitcoin_seed": "never",
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
