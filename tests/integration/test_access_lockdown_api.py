from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.access import get_access_session_context
from app.db.base import Base
from app.db.models.access import AccessSession, ChildApiKey, DelegatedPass
from app.db.session import get_db
from app.main import app


def _client(seed: bool = True, *, context: SimpleNamespace | None = None) -> TestClient:
    os.environ["ACCESS_SERVER_PEPPER"] = "lockdown-pepper"
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, class_=Session)
    if seed:
        db = SessionLocal()
        db.add(AccessSession(session_hash="hmac-sha256:s1", certificate_fingerprint="sha256:cert", device_key_fingerprint="sha256:device", scopes_json=["api:keys:manage"], status="active", created_at=datetime.now(UTC), updated_at=datetime.now(UTC), expires_at=datetime.now(UTC) + timedelta(hours=1)))
        db.add(ChildApiKey(parent_pass_lookup_hash="hmac-sha256:pass", key_id_hash="hmac-sha256:key", key_secret_hash="hmac-sha256:key-secret", name="bot", scopes_json=["market:intelligence:read"], limits_json={}, cannot_access_json=[], status="active", expires_at=datetime.now(UTC) + timedelta(days=1)))
        db.add(DelegatedPass(parent_pass_lookup_hash="hmac-sha256:pass", delegated_pass_hash="hmac-sha256:delegated", delegated_to_hash=None, scopes_json=["market:intelligence:read"], constraints_json={}, status="active", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC) + timedelta(days=1)))
        db.commit()
        db.close()

    def override_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_context():
        return context or SimpleNamespace(pass_lookup_hash="hmac-sha256:pass", certificate_fingerprint="sha256:cert", session_hash="hmac-sha256:actor", plan_code="pro_pass", scopes=["api:keys:manage"], expires_at=datetime.now(UTC) + timedelta(hours=1), device_key_fingerprint="sha256:device")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_access_session_context] = override_context
    return TestClient(app)


def test_post_access_lockdown_returns_counts_and_audit_hash() -> None:
    client = _client()
    try:
        response = client.post("/api/v1/access/lockdown", json={"scope": "current_pass", "reason": "suspected_device_compromise", "confirmation_intent_signature": "intent", "recovery_mode": True})
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "locked_down"
        assert payload["lockdown_id"].startswith("lock_")
        assert payload["affected_sessions"] == 1
        assert payload["affected_child_api_keys"] == 1
        assert payload["affected_delegated_passes"] == 1
        assert payload["audit_event_hash"]
    finally:
        app.dependency_overrides.clear()


def test_lockdown_missing_session_fails() -> None:
    app.dependency_overrides.clear()
    response = TestClient(app).post("/api/v1/access/lockdown", json={"scope": "current_pass", "confirmation_intent_signature": "intent"})
    assert response.status_code in {401, 403}


def test_lockdown_missing_human_intent_signature_fails() -> None:
    client = _client()
    try:
        response = client.post("/api/v1/access/lockdown", json={"scope": "current_pass"})
        assert response.status_code == 403
        assert "step_up" in response.text or "human_intent" in response.text
    finally:
        app.dependency_overrides.clear()


def test_recovery_status_endpoint_remains_reachable_after_lockdown() -> None:
    client = _client()
    try:
        client.post("/api/v1/access/lockdown", json={"scope": "current_pass", "confirmation_intent_signature": "intent"})
        response = client.get("/api/v1/access/recovery/status/recovery-attempt-id")
        assert response.status_code in {200, 403, 404}
        assert response.status_code != 401
    finally:
        app.dependency_overrides.clear()
