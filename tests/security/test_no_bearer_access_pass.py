from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

RAW_PASS = "bbp_live_test_access_pass_secret"


def test_raw_access_pass_is_not_bearer_authorization_material() -> None:
    source = Path("app/api/access_dependencies.py").read_text()

    assert RAW_PASS.startswith("bbp_live_")
    assert "access_legacy_bearer_rejected" in source
    assert "Authorization" not in Path("app/services/access/certificate_issuer.py").read_text()


def test_raw_access_pass_bearer_is_rejected_by_protected_endpoint_without_enumeration() -> None:
    response = TestClient(app).get(
        "/api/v1/treasury/requests",
        headers={"Authorization": f"Bearer {RAW_PASS}"},
    )

    assert response.status_code in {401, 403}
    assert RAW_PASS not in response.text
    assert "access_token" not in response.text.lower()


def test_x_bastion_pass_does_not_grant_session_access() -> None:
    response = TestClient(app).get("/api/v1/access/me", headers={"X-Bastion-Pass": RAW_PASS})

    assert response.status_code == 401
    assert RAW_PASS not in response.text
    assert "session" in response.text.lower()


def test_missing_request_signature_is_rejected_for_protected_request() -> None:
    response = TestClient(app).get(
        "/api/v1/treasury/requests",
        headers={"X-Bastion-Session": "sess_test_without_signature"},
    )

    assert response.status_code in {401, 403}
    assert "bbp_live" not in response.text


def test_importing_or_holding_pass_material_is_not_authentication() -> None:
    issuer_source = Path("app/services/access/certificate_issuer.py").read_text().lower()
    request_verifier_source = Path("app/services/access/request_verifier.py").read_text().lower()

    assert "def authenticate" not in issuer_source
    assert "authorization: bearer" in request_verifier_source
    assert "x-bastion-session" in request_verifier_source
    assert "x-bastion-signature" in request_verifier_source
