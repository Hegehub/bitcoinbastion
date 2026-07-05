from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

PREMIUM_ROUTER_FILES = [
    Path("app/api/v1/admin.py"),
    Path("app/api/v1/entities.py"),
    Path("app/api/v1/metrics_status.py"),
    Path("app/api/v1/observability.py"),
    Path("app/api/v1/operations.py"),
    Path("app/api/v1/operator_signals.py"),
    Path("app/api/v1/plugins.py"),
    Path("app/api/v1/policy.py"),
    Path("app/api/v1/trace.py"),
    Path("app/api/v1/treasury.py"),
    Path("app/api/v1/users.py"),
    Path("app/api/v1/wallet.py"),
    Path("app/api/v1/webhooks.py"),
]


def test_no_premium_router_uses_legacy_user_dependencies() -> None:
    for path in PREMIUM_ROUTER_FILES:
        source = path.read_text()
        assert "get_current_user" not in source
        assert "get_admin_user" not in source
        assert "Authorization: Bearer" not in source


def test_openapi_marks_protected_premium_routes_as_proof_of_access() -> None:
    schema = TestClient(app).get("/openapi.json").json()
    for route in (
        "/api/v1/trace/business/profile",
        "/api/v1/trace/enterprise/profile",
        "/api/v1/treasury/requests",
        "/api/v1/webhooks",
        "/api/v1/admin/status",
    ):
        operation = next(iter(schema["paths"][route].values()))
        assert operation["x-proof-of-access-required"] is True
        assert "BastionProofOfAccessSession" in str(operation.get("security"))


def test_openapi_documents_human_intent_signature_scheme() -> None:
    schema = TestClient(app).get("/openapi.json").json()
    schemes = schema["components"]["securitySchemes"]
    assert "BastionHumanIntentSignature" in schemes
    assert schemes["BastionHumanIntentSignature"]["name"] == "X-Bastion-Intent-Signature"
