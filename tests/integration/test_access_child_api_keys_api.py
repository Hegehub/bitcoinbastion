import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.api.v1.access import get_access_session_context


def _client(plan: str = "pro_pass", scopes: list[str] | None = None) -> TestClient:
    os.environ["ACCESS_SERVER_PEPPER"] = "child-key-pepper"
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, class_=Session)

    def override_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_context():
        return SimpleNamespace(
            pass_lookup_hash="hmac-sha256:parent",
            certificate_fingerprint="sha256:cert",
            plan_code=plan,
            scopes=scopes or ["market:intelligence:read", "api:keys:manage", "delegated_pass:create", "trace:standard:read"],
            expires_at=datetime.now(UTC) + timedelta(days=30),
            session_hash="hmac-sha256:session",
            device_key_fingerprint="sha256:device",
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_access_session_context] = override_context
    return TestClient(app)


def _payload(scope: str = "market:intelligence:read") -> dict[str, object]:
    return {"name": "bot", "scopes": [scope], "metric_entitlements": {"groups": ["market.intelligence"]}, "limits": {}, "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat()}


def test_child_api_key_create_list_revoke_and_rotate_flow() -> None:
    client = _client()
    try:
        created = client.post("/api/v1/access/api-keys", json=_payload(), headers={"X-Bastion-Intent-Signature": "intent"})
        assert created.status_code == 200
        raw_key = created.json()["raw_child_api_key"]
        key_id = created.json()["key_id"]
        assert raw_key.startswith("bbk_live_")
        listed = client.get("/api/v1/access/api-keys")
        assert listed.status_code == 200
        assert raw_key not in listed.text
        rotated = client.post(f"/api/v1/access/api-keys/{key_id}/rotate", headers={"X-Bastion-Intent-Signature": "intent"})
        assert rotated.status_code == 200
        assert rotated.json()["raw_child_api_key"] != raw_key
        deleted = client.delete(f"/api/v1/access/api-keys/{key_id}")
        assert deleted.status_code in {204, 404}
    finally:
        app.dependency_overrides.clear()


def test_child_key_creation_fails_for_lite_and_scope_escalation() -> None:
    client = _client(plan="lite_pass", scopes=["market:intelligence:read"])
    try:
        assert client.post("/api/v1/access/api-keys", json=_payload(), headers={"X-Bastion-Intent-Signature": "intent"}).status_code == 403
    finally:
        app.dependency_overrides.clear()
    client = _client(scopes=["market:intelligence:read", "api:keys:manage"])
    try:
        assert client.post("/api/v1/access/api-keys", json=_payload("treasury:read"), headers={"X-Bastion-Intent-Signature": "intent"}).status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_delegated_pass_create_list_revoke_flow() -> None:
    client = _client()
    try:
        response = client.post("/api/v1/access/delegated-passes", json={"name": "analyst", "scopes": ["market:intelligence:read"], "metric_entitlements": {"groups": ["market.intelligence"]}, "constraints": {}, "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat()}, headers={"X-Bastion-Intent-Signature": "intent"})
        assert response.status_code == 200
        raw_pass = response.json()["raw_delegated_pass"]
        delegated_id = response.json()["delegated_pass_id"]
        listed = client.get("/api/v1/access/delegated-passes")
        assert listed.status_code == 200
        assert raw_pass not in listed.text
        assert client.delete(f"/api/v1/access/delegated-passes/{delegated_id}").status_code == 204
    finally:
        app.dependency_overrides.clear()
