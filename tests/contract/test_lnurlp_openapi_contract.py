from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_lnurlp_path_is_documented_as_public_protocol_route() -> None:
    spec = TestClient(app).get("/openapi.json").json()
    assert "/.well-known/lnurlp/{name}" in spec["paths"]
    operation = spec["paths"]["/.well-known/lnurlp/{name}"]["get"]
    assert operation["tags"] == ["LNURL", "Lightning Address"]
    assert "payRequest" in operation["summary"] or "Lightning Address" in operation["summary"]


def test_lnurlp_route_returns_unwrapped_camelcase_protocol_fields() -> None:
    client = TestClient(app, headers={"host": "bitcoin-bastion.com"})
    response = client.get("/.well-known/lnurlp/pro")
    body = response.json()
    assert body["tag"] == "payRequest"
    assert "maxSendable" in body
    assert "minSendable" in body
    assert "commentAllowed" not in body or isinstance(body["commentAllowed"], int)
    assert "data" not in body
    assert "result" not in body
    assert "success" not in body


def test_lnurlp_error_schema_is_protocol_native() -> None:
    body = TestClient(app, headers={"host": "bitcoin-bastion.com"}).get("/.well-known/lnurlp/unknown").json()
    assert set(body) == {"status", "reason"}
    assert body["status"] == "ERROR"
