from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api import access_dependencies as deps
from app.core.exceptions import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.access.context import AccessContext
from app.main import app
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth.auth_service import AuthService


class _DB:
    pass


class _SessionContext:
    session_hash = "hmac-sha256:session"
    certificate_fingerprint = "sha256:cert"
    pass_lookup_hash = "hmac-sha256:pass"
    device_key_fingerprint = "sha256:device"
    plan_code = "plus_pass"
    scopes = ["market:intelligence:read"]
    expires_at = None
    risk_level = "low"
    requires_request_signing = True


def _error_code(response: object) -> str:
    data = response.json()  # type: ignore[attr-defined]
    if "error" in data:
        return data["error"]["code"]
    return data["detail"]["code"]


def test_register_endpoint_is_gone_and_does_not_accept_password_account_creation() -> None:
    response = TestClient(app).post(
        "/api/v1/auth/register",
        json={"email": "u@example.com", "username": "satoshi", "password": "password123"},
    )

    assert response.status_code == 410
    assert _error_code(response) == "legacy_auth_disabled"
    assert "password123" not in response.text


def test_login_endpoint_is_gone_and_does_not_issue_token() -> None:
    response = TestClient(app).post(
        "/api/v1/auth/login",
        json={"username": "satoshi", "password": "password123"},
    )

    assert response.status_code == 410
    assert _error_code(response) == "legacy_auth_disabled"
    assert "access_token" not in response.text
    assert "bearer" not in response.text.lower()


def test_legacy_auth_schemas_do_not_accept_password_or_return_access_token() -> None:
    assert "password" not in RegisterRequest.model_fields
    assert "password" not in LoginRequest.model_fields
    assert "access_token" not in TokenResponse.model_fields
    assert "token_type" not in TokenResponse.model_fields


def test_legacy_auth_service_and_security_helpers_fail_closed() -> None:
    service = AuthService(repo=None)
    with pytest.raises(AppError):
        service.register(RegisterRequest())
    with pytest.raises(AppError):
        service.login(LoginRequest())
    with pytest.raises(AppError):
        hash_password("password123")
    with pytest.raises(AppError):
        verify_password("password123", "hash")
    with pytest.raises(AppError):
        create_access_token("1")


def test_protected_dependency_rejects_authorization_bearer() -> None:
    test_app = FastAPI()

    @test_app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": {"code": exc.code, "message": exc.message}})

    @test_app.get("/protected")
    async def protected(_context: AccessContext = Depends(deps.require_access_session)) -> dict[str, bool]:
        return {"ok": True}

    test_app.dependency_overrides[deps.get_db] = lambda: _DB()
    response = TestClient(test_app).get("/protected", headers={"Authorization": "Bearer legacy-token"})

    assert response.status_code == 401
    assert _error_code(response) == "access_legacy_bearer_rejected"
    assert "legacy-token" not in response.text


def test_protected_dependency_accepts_valid_proof_of_access_session() -> None:
    test_app = FastAPI()

    @test_app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": {"code": exc.code, "message": exc.message}})

    @test_app.get("/protected")
    async def protected(context: AccessContext = Depends(deps.require_access_session)) -> dict[str, str]:
        return {"plan_code": context.plan_code.value}

    test_app.dependency_overrides[deps.get_db] = lambda: _DB()
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: _SessionContext()
    deps.REVOCATION_CHECKER = lambda _context, _db: {"allowed": True, "revoked_targets": []}
    try:
        response = TestClient(test_app).get("/protected", headers={"X-Bastion-Session": "raw-session-token"})
    finally:
        deps.SESSION_CONTEXT_RESOLVER = None
        deps.REVOCATION_CHECKER = None

    assert response.status_code == 200
    assert response.json()["plan_code"] == "plus_pass"
    assert "raw-session-token" not in response.text


def test_openapi_marks_legacy_auth_as_deprecated_and_access_has_no_password_or_seed_fields() -> None:
    schema = TestClient(app).get("/openapi.json").json()

    assert schema["paths"]["/api/v1/auth/login"]["post"]["deprecated"] is True
    assert schema["paths"]["/api/v1/auth/register"]["post"]["deprecated"] is True
    assert schema["paths"]["/api/v1/auth/login"]["post"]["x-legacy-auth-disabled"] is True

    serialized = str(schema["paths"]["/api/v1/access/payment-intents"])
    assert "password" not in serialized.lower()
    assert "bitcoin_seed" not in serialized.lower()
    assert "bitcoin_private_key" not in serialized.lower()

    schemes = schema["components"]["securitySchemes"]
    assert "BastionProofOfAccessSession" in schemes
    assert "BastionProofOfAccessSignature" in schemes
