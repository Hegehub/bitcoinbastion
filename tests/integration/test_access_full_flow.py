from __future__ import annotations


from fastapi.testclient import TestClient

from app.api.v1 import access as access_api
from app.db.models.access import AccessCertificate, SubscriptionEntitlement
from app.domain.access.scopes import MARKET_INTELLIGENCE_READ
from app.main import app
from tests.integration.test_access_api import (
    TestingSessionLocal,
    _ChallengeService,
    _Context,
    _EntitlementService,
    _PaidIssuer,
    _PaymentService,
    _SessionService,
    _UnpaidIssuer,
    _override_db,
    setup_function,
    teardown_function,
)


def test_access_full_happy_path_and_show_once_secret() -> None:
    setup_function()
    try:
        db = TestingSessionLocal()
        payment_service = _PaymentService()
        issuer = _PaidIssuer(db)
        session_service = _SessionService()
        app.dependency_overrides[access_api.get_payment_intent_service] = lambda: payment_service
        app.dependency_overrides[access_api.get_db] = _override_db(db)
        app.dependency_overrides[access_api.get_certificate_issuer] = lambda: issuer
        app.dependency_overrides[access_api.get_entitlement_service] = lambda: _EntitlementService(db)
        app.dependency_overrides[access_api.get_challenge_service] = lambda: _ChallengeService()
        app.dependency_overrides[access_api.get_session_service] = lambda: session_service
        app.dependency_overrides[access_api.get_access_session_context] = lambda: _Context()
        client = TestClient(app)

        intent = client.post(
            "/api/v1/access/payment-intents",
            json={"plan_code": "plus_pass", "payment_method": "manual", "amount_sats": 1000},
        )
        assert intent.status_code == 201
        payment_intent_id = intent.json()["payment_intent_id"]

        first_certificate = client.post(
            "/api/v1/access/certificates",
            json={
                "payment_intent_id": payment_intent_id,
                "device_public_key": "test-device-public-key",
                "device_key_fingerprint": "sha256:device-api",
                "requested_origin": "https://app.example.test",
            },
        )
        second_certificate = client.post(
            "/api/v1/access/certificates",
            json={
                "payment_intent_id": payment_intent_id,
                "device_public_key": "test-device-public-key",
                "device_key_fingerprint": "sha256:device-api",
                "requested_origin": "https://app.example.test",
            },
        )
        assert first_certificate.status_code == 200
        assert first_certificate.json()["raw_access_pass"] == "bbp_live_test_pass_once"
        assert second_certificate.status_code == 200
        assert second_certificate.json()["raw_access_pass"] is None

        challenge = client.post(
            "/api/v1/access/challenges",
            json={
                "certificate_fingerprint": "sha256:cert-api",
                "origin": "https://app.example.test",
                "requested_scopes": [MARKET_INTELLIGENCE_READ],
                "device_key_fingerprint": "sha256:device-api",
            },
        )
        assert challenge.status_code == 200
        assert challenge.json()["challenge_payload"]["origin"] == "https://app.example.test"

        session = client.post(
            "/api/v1/access/sessions",
            json={
                "challenge_id": "challenge-1",
                "certificate_fingerprint": "sha256:cert-api",
                "origin": "https://app.example.test",
                "device_key_fingerprint": "sha256:device-api",
                "challenge_signature": "test-signature",
            },
        )
        assert session.status_code == 200
        assert session.json()["session_token"] == "session-token-once"

        me = client.get("/api/v1/access/me", headers={"X-Bastion-Session": session.json()["session_token"]})
        assert me.status_code == 200
        assert me.json()["plan_code"] == "plus_pass"

        assert db.query(AccessCertificate).count() == 1
        assert db.query(SubscriptionEntitlement).count() == 1
        assert "bbp_live_test_pass_once" not in str(db.query(AccessCertificate).first().__dict__)
    finally:
        teardown_function()


def test_access_full_flow_failure_paths_are_deterministic() -> None:
    setup_function()
    try:
        app.dependency_overrides[access_api.get_certificate_issuer] = lambda: _UnpaidIssuer()
        app.dependency_overrides[access_api.get_entitlement_service] = lambda: _EntitlementService(
            TestingSessionLocal()
        )
        client = TestClient(app)

        unpaid = client.post(
            "/api/v1/access/certificates",
            json={"payment_intent_id": 999, "device_public_key": "pub"},
        )
        assert unpaid.status_code == 402
        assert "raw_access_pass" not in unpaid.text

        app.dependency_overrides[access_api.get_challenge_service] = lambda: _ChallengeService()
        scope_escalation = client.post(
            "/api/v1/access/challenges",
            json={
                "certificate_fingerprint": "sha256:cert-api",
                "origin": "https://app.example.test",
                "requested_scopes": ["signals:advanced:read"],
            },
        )
        assert scope_escalation.status_code == 403

        service = _SessionService()
        app.dependency_overrides[access_api.get_session_service] = lambda: service
        payload = {
            "challenge_id": "challenge-1",
            "certificate_fingerprint": "sha256:cert-api",
            "origin": "https://app.example.test",
            "device_key_fingerprint": "sha256:device-api",
            "challenge_signature": "test-signature",
        }
        first = client.post("/api/v1/access/sessions", json=payload)
        reused = client.post("/api/v1/access/sessions", json=payload)
        assert first.status_code == 200
        assert reused.status_code == 403
    finally:
        teardown_function()


def test_missing_session_fails_access_me() -> None:
    setup_function()
    try:
        response = TestClient(app).get("/api/v1/access/me")
        assert response.status_code in {401, 403, 503}
        assert "raw_access_pass" not in response.text
    finally:
        teardown_function()
