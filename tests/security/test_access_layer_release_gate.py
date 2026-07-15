from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sdk/python"))
from bitcoin_bastion_sdk.auth import LegacyAuthDisabledError, build_headers  # noqa: E402


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="ignore")


def test_release_gate_legacy_auth_endpoints_fail_closed() -> None:
    client = TestClient(app)
    for endpoint, payload in (
        ("/api/v1/auth/login", {"username": "legacy", "password": "not-allowed"}),
        ("/api/v1/auth/register", {"email": "legacy@example.invalid", "password": "not-allowed"}),
    ):
        response = client.post(endpoint, json=payload)
        rendered = response.text.lower()
        assert response.status_code == 410
        assert "legacy_auth_disabled" in rendered
        assert "access_token" not in rendered
        assert "token_type" not in rendered


def test_release_gate_raw_access_pass_and_bearer_do_not_unlock_protected_api() -> None:
    raw_pass = "bbp_live_release_gate_secret"
    response = TestClient(app).get(
        "/api/v1/treasury/requests",
        headers={"Authorization": f"Bearer {raw_pass}", "X-Bastion-Pass": raw_pass},
    )

    assert response.status_code in {401, 403}
    assert raw_pass not in response.text
    assert "access_token" not in response.text.lower()


def test_release_gate_openapi_marks_legacy_auth_disabled_and_documents_pop_headers() -> None:
    spec = TestClient(app).get("/openapi.json").json()
    auth_paths = spec["paths"].get("/api/v1/auth/login", {})
    serialized_auth = str(auth_paths).lower()
    serialized_spec = str(spec).lower()

    assert "x-legacy-auth-disabled" in serialized_auth
    assert "access_token" not in serialized_auth
    for header in (
        "x-bastion-session",
        "x-bastion-timestamp",
        "x-bastion-nonce",
        "x-bastion-body-hash",
        "x-bastion-signature",
    ):
        assert header in serialized_spec


def test_release_gate_sdks_fail_closed_for_legacy_bearer_even_with_flags() -> None:
    with pytest.raises(LegacyAuthDisabledError):
        build_headers("legacy", allow_legacy_bearer_auth=True)

    ts_auth = _read("sdk/typescript/src/auth.ts")
    assert "return { Authorization:" not in ts_auth
    assert "throw new LegacyAuthDisabledError()" in ts_auth


def test_release_gate_frontend_has_access_flow_without_password_form() -> None:
    access_ui = _read("frontend/bastion_ui/routes/access.py")

    assert "This is not a password." in access_ui
    assert "Bastion will never ask for your Bitcoin" in access_ui
    assert 'type="password"' not in access_ui
    assert "authorization: bearer" not in access_ui.lower()


def test_release_gate_remaining_legacy_terms_are_classified_safe() -> None:
    classified_docs = [
        "docs/ACCESS_LAYER_RELEASE_GATE.md",
        "docs/ACCESS_LAYER.md",
        "docs/PUBLIC_API_SECURITY.md",
        "docs/ACCESS_REQUEST_SIGNING.md",
        "docs/SDK_PYTHON_ACCESS_AUTH.md",
        "docs/SDK_TYPESCRIPT_ACCESS_AUTH_MIGRATION.md",
    ]

    for path in classified_docs:
        text = _read(path).lower()
        assert "proof-of-access" in text or "legacy" in text

    active_auth_sources = "\n".join(
        _read(path)
        for path in [
            "app/api/v1/auth.py",
            "app/core/security.py",
            "app/services/auth/auth_service.py",
            "app/api/dependencies.py",
        ]
    ).lower()
    assert "legacy_auth_disabled" in active_auth_sources
    assert "jwt.encode" not in active_auth_sources
    assert "verify_password(" in active_auth_sources  # fail-closed import-stability shim only
