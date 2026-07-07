from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


ACCESS_ENDPOINTS = {
    "/api/v1/access/payment-intents",
    "/api/v1/access/payment-intents/{payment_intent_id}",
    "/api/v1/access/certificates",
    "/api/v1/access/challenges",
    "/api/v1/access/sessions",
    "/api/v1/access/me",
    "/api/v1/access/me/entitlements",
    "/api/v1/access/me/limits",
    "/api/v1/access/lockdown",
}

PROOF_HEADERS = {
    "X-Bastion-Session",
    "X-Bastion-Timestamp",
    "X-Bastion-Nonce",
    "X-Bastion-Body-Hash",
    "X-Bastion-Signature",
}


def test_access_openapi_contract() -> None:
    spec = TestClient(app).get("/openapi.json").json()
    paths = spec["paths"]
    assert ACCESS_ENDPOINTS.issubset(paths)

    security_schemes = spec.get("components", {}).get("securitySchemes", {})
    assert "BastionPoPSession" in security_schemes
    assert "BastionRequestSignature" in security_schemes
    assert security_schemes["BastionPoPSession"]["name"] == "X-Bastion-Session"
    assert security_schemes["BastionRequestSignature"]["name"] == "X-Bastion-Signature"

    access_schema_names = [
        name for name in spec.get("components", {}).get("schemas", {}) if name.startswith("Access")
    ]
    access_schemas = {name: spec["components"]["schemas"][name] for name in access_schema_names}
    schemas_text = str(access_schemas).lower()
    assert "bitcoin_seed" not in schemas_text
    assert "bitcoin_private_key" not in schemas_text
    assert "password" not in schemas_text
    assert "bearer access pass" not in schemas_text


def test_legacy_auth_openapi_is_deprecated_disabled_not_primary_auth() -> None:
    spec = TestClient(app).get("/openapi.json").json()
    login = spec["paths"]["/api/v1/auth/login"]["post"]
    register = spec["paths"]["/api/v1/auth/register"]["post"]
    for operation in (login, register):
        assert operation.get("deprecated") is True
        assert operation.get("x-legacy-auth-disabled") is True
        assert operation.get("x-replacement") == "/api/v1/access/payment-intents"
        text = str(operation).lower()
        assert "bearer access pass" not in text
        assert "active authentication" not in text


def test_proof_of_access_headers_are_documented_on_protected_operations() -> None:
    spec = TestClient(app).get("/openapi.json").json()
    operation = spec["paths"]["/api/v1/treasury/requests"]["get"]
    assert operation.get("x-proof-of-access-required") is True
    documented = {param["name"] for param in operation.get("parameters", [])}
    assert PROOF_HEADERS.issubset(documented)


def test_access_docs_avoid_bearer_access_pass_and_bitcoin_seed_auth() -> None:
    docs = [
        "docs/ACCESS_LAYER.md",
        "docs/API_ACCESS.md",
        "docs/ACCESS_REQUEST_SIGNING.md",
        "docs/ACCESS_RECOVERY.md",
        "docs/ACCESS_ENVIRONMENT.md",
    ]
    combined = "\n".join(open(path, encoding="utf-8").read().lower() for path in docs)
    assert "bearer access pass" not in combined
    assert "authorization: bearer <access_pass>" not in combined
    assert "enter your bitcoin seed" not in combined
    assert "use your wallet seed to recover bastion" not in combined
    assert "support can recover your account" not in combined
    assert "bastion recovery seed is not your bitcoin wallet seed" in combined
    assert "bastion will never ask for your bitcoin" in combined
