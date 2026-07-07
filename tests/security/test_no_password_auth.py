from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

client = TestClient(app)


def _assert_legacy_disabled(response) -> None:  # type: ignore[no-untyped-def]
    assert response.status_code in {403, 410}
    body = response.json()
    rendered = str(body).lower()
    assert "legacy_auth_disabled" in rendered
    assert "access_token" not in rendered
    assert 'token_type": "bearer' not in rendered


def test_password_login_is_disabled_and_cannot_issue_bearer_token() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "legacy", "password": "not-allowed"},
    )

    _assert_legacy_disabled(response)


def test_password_register_is_disabled_and_cannot_create_account() -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "legacy@example.invalid", "username": "legacy", "password": "not-allowed"},
    )

    _assert_legacy_disabled(response)


def test_password_fields_are_not_accepted_by_active_access_endpoints() -> None:
    response = client.post(
        "/api/v1/access/payment-intents",
        json={"plan_code": "lite_pass", "payment_method": "manual", "password": "not-allowed"},
    )

    assert response.status_code in {400, 422}
    assert "access_token" not in response.text.lower()
    assert "bearer" not in response.text.lower()


def test_legacy_auth_schemas_are_marked_deprecated_compatibility_only() -> None:
    assert RegisterRequest.model_fields["deprecated"].default is True
    assert LoginRequest.model_fields["deprecated"].default is True
    token = TokenResponse()
    assert token.code == "legacy_auth_disabled"
    assert not hasattr(token, "access_token")


def test_password_reset_fallback_is_not_available_in_openapi() -> None:
    spec = client.get("/openapi.json").json()
    paths = {path.lower() for path in spec["paths"]}

    assert "/api/v1/auth/password-reset" not in paths
    assert "/api/v1/auth/forgot-password" not in paths
    assert "/api/v1/auth/reset" not in paths
