from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api import access_dependencies as deps
from app.core.exceptions import AppError
from app.domain.access.context import AccessContext
from app.domain.access.plans import PlanCode
from app.domain.access.scopes import MARKET_INTELLIGENCE_READ, METRICS_BASIC_READ
from app.services.access.policy_context import AccessPolicyDecision


@dataclass
class _SessionContext:
    session_hash: str = "hmac-sha256:session"
    certificate_fingerprint: str = "sha256:cert"
    pass_lookup_hash: str = "hmac-sha256:pass"
    device_key_fingerprint: str = "sha256:device"
    plan_code: str = "plus_pass"
    scopes: list[str] = None  # type: ignore[assignment]
    expires_at: datetime = datetime.now(UTC) + timedelta(minutes=15)
    risk_level: str = "low"
    requires_request_signing: bool = True

    def __post_init__(self) -> None:
        if self.scopes is None:
            self.scopes = [MARKET_INTELLIGENCE_READ, METRICS_BASIC_READ]


class _PolicyEngine:
    calls = 0

    def evaluate(self, context: Any) -> AccessPolicyDecision:
        self.__class__.calls += 1
        return AccessPolicyDecision(decision="allow", allowed=True, reason_code="access_allowed", human_reason="ok")


class _DenyPolicyEngine:
    def evaluate(self, context: Any) -> AccessPolicyDecision:
        return AccessPolicyDecision(decision="deny", allowed=False, reason_code="scope_not_allowed", human_reason="denied")


class _DB:
    pass


def _app() -> FastAPI:
    app = FastAPI()

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": {"code": exc.code, "message": exc.message}})

    @app.get("/public")
    def public() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/session")
    async def session(context: AccessContext = Depends(deps.require_access_session)) -> dict[str, str]:
        return {"plan_code": context.plan_code.value}

    @app.get("/scope")
    async def scope(context: AccessContext = Depends(deps.require_scope(MARKET_INTELLIGENCE_READ))) -> dict[str, bool]:
        return {"ok": True}

    @app.get("/plan")
    async def plan(context: AccessContext = Depends(deps.require_plan(PlanCode.PRO))) -> dict[str, bool]:
        return {"ok": True}

    @app.get("/metric")
    async def metric(context: AccessContext = Depends(deps.require_metric_entitlement("signals.advanced"))) -> dict[str, bool]:
        return {"ok": True}

    @app.post("/critical")
    async def critical(context: AccessContext = Depends(deps.require_step_up_for_critical_action("create_api_key"))) -> dict[str, bool]:
        return {"ok": True}

    return app


@pytest.fixture(autouse=True)
def _reset() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: _SessionContext()
    deps.REVOCATION_CHECKER = lambda _context, _db: {"allowed": True, "revoked_targets": []}
    deps.REQUEST_SIGNATURE_VERIFIER = None
    deps.POLICY_ENGINE_FACTORY = _PolicyEngine
    yield
    deps.SESSION_CONTEXT_RESOLVER = None
    deps.REVOCATION_CHECKER = None
    deps.REQUEST_SIGNATURE_VERIFIER = None
    deps.POLICY_ENGINE_FACTORY = deps.AccessPolicyEngine


def _client() -> TestClient:
    app = _app()
    app.dependency_overrides[deps.get_db] = lambda: _DB()
    return TestClient(app)


def test_missing_access_headers_are_rejected() -> None:
    response = _client().get("/session")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == deps.ACCESS_SESSION_MISSING


def test_authorization_bearer_is_rejected_as_access_layer_credential() -> None:
    response = _client().get("/session", headers={"Authorization": "Bearer bbp_live_secret"})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == deps.ACCESS_LEGACY_BEARER_REJECTED


def test_invalid_session_is_rejected() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: (_ for _ in ()).throw(RuntimeError("invalid"))
    response = _client().get("/session", headers={"X-Bastion-Session": "raw-session-token"})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == deps.ACCESS_SESSION_INVALID


def test_expired_session_is_rejected() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: (_ for _ in ()).throw(RuntimeError("expired"))
    response = _client().get("/session", headers={"X-Bastion-Session": "raw-session-token"})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == deps.ACCESS_SESSION_EXPIRED


def test_revoked_session_is_rejected() -> None:
    deps.REVOCATION_CHECKER = lambda _context, _db: {"allowed": False, "revoked_targets": [{"target_type": "session"}]}
    response = _client().get("/session", headers={"X-Bastion-Session": "raw-session-token"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == deps.ACCESS_SESSION_REVOKED


def test_active_session_succeeds_and_revocation_is_called() -> None:
    called = {"revocation": False}
    deps.REVOCATION_CHECKER = lambda _context, _db: called.update(revocation=True) or {"allowed": True, "revoked_targets": []}
    response = _client().get("/session", headers={"X-Bastion-Session": "raw-session-token"})
    assert response.status_code == 200
    assert called["revocation"] is True


def test_missing_scope_is_denied() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: _SessionContext(scopes=[METRICS_BASIC_READ])
    response = _client().get("/scope", headers={"X-Bastion-Session": "raw-session-token"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == deps.ACCESS_SCOPE_MISSING


def test_lower_plan_receives_upgrade_required() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: _SessionContext(plan_code="lite_pass")
    response = _client().get("/plan", headers={"X-Bastion-Session": "raw-session-token"})
    assert response.status_code == 402
    assert response.json()["detail"]["code"] == deps.ACCESS_UPGRADE_REQUIRED


def test_missing_metric_entitlement_receives_metric_not_allowed_or_upgrade() -> None:
    response = _client().get("/metric", headers={"X-Bastion-Session": "raw-session-token"})
    assert response.status_code in {402, 403}
    assert response.json()["detail"]["code"] in {deps.ACCESS_METRIC_NOT_ALLOWED, deps.ACCESS_UPGRADE_REQUIRED}


def test_critical_action_without_request_signature_receives_step_up_required() -> None:
    response = _client().post("/critical", headers={"X-Bastion-Session": "raw-session-token"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == deps.ACCESS_SIGNATURE_REQUIRED


def test_policy_engine_is_called_for_protected_dependency() -> None:
    _PolicyEngine.calls = 0
    response = _client().get("/scope", headers={"X-Bastion-Session": "raw-session-token"})
    assert response.status_code == 200
    assert _PolicyEngine.calls == 1


def test_policy_denial_is_translated_to_api_error() -> None:
    deps.POLICY_ENGINE_FACTORY = _DenyPolicyEngine
    response = _client().get("/scope", headers={"X-Bastion-Session": "raw-session-token"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == deps.ACCESS_SCOPE_MISSING


def test_raw_session_or_pass_not_in_error_response() -> None:
    response = _client().get("/session", headers={"Authorization": "Bearer bbp_live_secret", "X-Bastion-Session": "raw-session-token"})
    body = response.text
    assert "bbp_live_secret" not in body
    assert "raw-session-token" not in body


def test_public_endpoint_remains_accessible_without_auth() -> None:
    response = _client().get("/public")
    assert response.status_code == 200
