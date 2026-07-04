from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_access_openapi_contract() -> None:
    spec = TestClient(app).get("/openapi.json").json()
    paths = spec["paths"]
    for path in [
        "/api/v1/access/payment-intents",
        "/api/v1/access/certificates",
        "/api/v1/access/challenges",
        "/api/v1/access/sessions",
        "/api/v1/access/me",
    ]:
        assert path in paths
    access_schema_names = [name for name in spec.get("components", {}).get("schemas", {}) if name.startswith("Access")]
    access_schemas = {name: spec["components"]["schemas"][name] for name in access_schema_names}
    schemas_text = str(access_schemas).lower()
    assert "bitcoin_seed" not in schemas_text
    assert "bitcoin_private_key" not in schemas_text
    assert "password" not in schemas_text
    assert "bearer access pass" not in schemas_text
