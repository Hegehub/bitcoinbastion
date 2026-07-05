from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import access_dependencies as deps
from app.domain.access.plans import PlanCode
from app.main import app
from app.services.access.plan_entitlements import build_entitlement_overlay
from app.services.access.policy_context import AccessPolicyDecision


@dataclass
class _SessionContext:
    plan_code: str = "business_pass"
    scopes: list[str] = field(default_factory=list)
    session_hash: str = "hmac-sha256:session"
    certificate_fingerprint: str = "sha256:cert"
    pass_lookup_hash: str = "hmac-sha256:pass"
    device_key_fingerprint: str = "sha256:device"
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(minutes=15))
    risk_level: str = "low"
    requires_request_signing: bool = True
    policy_mode: str = "proof_of_access"

    def __post_init__(self) -> None:
        if not self.scopes:
            self.scopes = list(
                build_entitlement_overlay(PlanCode(self.plan_code))["allowed_scopes"]
            )


class _AllowPolicyEngine:
    calls = 0

    def evaluate(self, context: Any) -> AccessPolicyDecision:
        self.__class__.calls += 1
        return AccessPolicyDecision(
            decision="allow", allowed=True, reason_code="access_allowed", human_reason="ok"
        )


@pytest.fixture(autouse=True)
def _reset_access_dependencies() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: _SessionContext()
    deps.REVOCATION_CHECKER = lambda _context, _db: {"allowed": True, "revoked_targets": []}
    deps.REQUEST_SIGNATURE_VERIFIER = None
    deps.POLICY_ENGINE_FACTORY = _AllowPolicyEngine
    _AllowPolicyEngine.calls = 0
    yield
    deps.SESSION_CONTEXT_RESOLVER = None
    deps.REVOCATION_CHECKER = None
    deps.REQUEST_SIGNATURE_VERIFIER = None
    deps.POLICY_ENGINE_FACTORY = deps.AccessPolicyEngine


def _client() -> TestClient:
    return TestClient(app)


def _code(response: Any) -> str:
    payload = response.json()
    if "error" in payload:
        return payload["error"]["code"]
    if "detail" in payload and isinstance(payload["detail"], dict):
        return payload["detail"]["code"]
    return payload.get("code", "")


def test_public_endpoints_remain_accessible_without_access_session() -> None:
    response = _client().get("/api/v1/health/live")
    assert response.status_code == 200


def test_premium_endpoint_rejects_missing_session() -> None:
    response = _client().get("/api/v1/trace/business/profile")
    assert response.status_code == 401
    assert _code(response) == deps.ACCESS_SESSION_MISSING


def test_premium_endpoint_rejects_invalid_session() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: (_ for _ in ()).throw(
        RuntimeError("invalid")
    )
    response = _client().get(
        "/api/v1/trace/business/profile", headers={"X-Bastion-Session": "raw-session"}
    )
    assert response.status_code == 401
    assert _code(response) == deps.ACCESS_SESSION_INVALID


def test_premium_endpoint_rejects_expired_session() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: (_ for _ in ()).throw(
        RuntimeError("expired")
    )
    response = _client().get(
        "/api/v1/trace/business/profile", headers={"X-Bastion-Session": "raw-session"}
    )
    assert response.status_code == 401
    assert _code(response) == deps.ACCESS_SESSION_EXPIRED


def test_premium_endpoint_rejects_revoked_session() -> None:
    deps.REVOCATION_CHECKER = lambda _context, _db: {
        "allowed": False,
        "revoked_targets": [{"target_type": "session"}],
    }
    response = _client().get(
        "/api/v1/trace/business/profile", headers={"X-Bastion-Session": "raw-session"}
    )
    assert response.status_code == 403
    assert _code(response) == deps.ACCESS_SESSION_REVOKED


def test_lite_session_cannot_access_pro_endpoint() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: _SessionContext(plan_code="lite_pass")
    response = _client().get(
        "/api/v1/treasury/requests", headers={"X-Bastion-Session": "raw-session"}
    )
    assert response.status_code in {402, 403}
    assert _code(response) in {deps.ACCESS_UPGRADE_REQUIRED, deps.ACCESS_SCOPE_MISSING}


def test_plus_session_cannot_access_business_endpoint() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: _SessionContext(plan_code="plus_pass")
    response = _client().get(
        "/api/v1/trace/business/profile", headers={"X-Bastion-Session": "raw-session"}
    )
    assert response.status_code == 402
    assert _code(response) == deps.ACCESS_UPGRADE_REQUIRED


def test_business_session_cannot_access_enterprise_endpoint() -> None:
    response = _client().get(
        "/api/v1/trace/enterprise/profile", headers={"X-Bastion-Session": "raw-session"}
    )
    assert response.status_code == 402
    assert _code(response) == deps.ACCESS_UPGRADE_REQUIRED


def test_correct_plan_and_scope_succeeds() -> None:
    response = _client().get(
        "/api/v1/trace/business/profile", headers={"X-Bastion-Session": "raw-session"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_missing_metric_entitlement_returns_metric_not_allowed() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: _SessionContext(plan_code="lite_pass")
    response = _client().get("/api/v1/metrics/usage", headers={"X-Bastion-Session": "raw-session"})
    assert response.status_code in {402, 403}
    assert _code(response) in {deps.ACCESS_METRIC_NOT_ALLOWED, deps.ACCESS_UPGRADE_REQUIRED}


def test_critical_action_without_signed_request_returns_signature_required() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: _SessionContext(plan_code="enterprise_pass")
    response = _client().post(
        "/api/v1/trace/enterprise/proof-packet?report_id=1",
        headers={"X-Bastion-Session": "raw-session"},
    )
    assert response.status_code == 403
    assert _code(response) == deps.ACCESS_SIGNATURE_REQUIRED


def test_critical_action_without_human_intent_fails() -> None:
    deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: _SessionContext(plan_code="enterprise_pass")

    def _signed_context(request: Any, db: Any) -> Any:
        context = deps._context_from_session("raw-session", request, db)  # noqa: SLF001
        return replace(context, is_request_signature_verified=True)

    deps.REQUEST_SIGNATURE_VERIFIER = _signed_context
    response = _client().post(
        "/api/v1/trace/enterprise/proof-packet?report_id=1",
        headers={
            "X-Bastion-Session": "raw-session",
            "X-Bastion-Timestamp": "2026-07-04T00:00:00Z",
            "X-Bastion-Nonce": "nonce",
            "X-Bastion-Body-Hash": "sha256:" + "0" * 64,
            "X-Bastion-Signature": "sig",
        },
    )
    assert response.status_code == 403
    assert _code(response) == deps.ACCESS_STEP_UP_REQUIRED


def test_policy_engine_is_called_for_protected_endpoint() -> None:
    response = _client().get(
        "/api/v1/trace/business/profile", headers={"X-Bastion-Session": "raw-session"}
    )
    assert response.status_code == 200
    assert _AllowPolicyEngine.calls >= 1


def test_legacy_authorization_bearer_does_not_unlock_protected_endpoint() -> None:
    response = _client().get(
        "/api/v1/trace/business/profile", headers={"Authorization": "Bearer legacy"}
    )
    assert response.status_code == 401
    assert _code(response) == deps.ACCESS_LEGACY_BEARER_REJECTED
    assert "Bearer legacy" not in response.text
