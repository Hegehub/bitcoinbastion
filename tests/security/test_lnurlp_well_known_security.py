from __future__ import annotations

import json
from dataclasses import replace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.well_known import lnurlp
from app.services.lnurl.lightning_address_service import LightningAddressService, LightningAddressServiceConfig


def build_service() -> LightningAddressService:
    service = LightningAddressService(config=LightningAddressServiceConfig(primary_domain="bitcoin-bastion.com"))
    service.create_product_address(local_part="pro")
    return service


def client_for(service: LightningAddressService) -> TestClient:
    lnurlp._RATE_BUCKETS.clear()
    app = FastAPI()
    app.include_router(lnurlp.router)
    app.dependency_overrides[lnurlp.get_lightning_address_service] = lambda: service
    return TestClient(app, headers={"host": "bitcoin-bastion.com"})


def test_host_header_injection_does_not_change_callback_host() -> None:
    client = client_for(build_service())
    response = client.get("/.well-known/lnurlp/pro", headers={"host": "attacker.example"})
    body = response.json()
    assert body.get("callback", "").find("attacker.example") == -1
    assert body["status"] == "ERROR"


def test_forwarded_headers_cannot_substitute_or_downgrade_callback() -> None:
    client = client_for(build_service())
    bad_host = client.get("/.well-known/lnurlp/pro", headers={"x-forwarded-host": "attacker.example"})
    assert bad_host.json()["status"] == "ERROR"
    downgraded = client.get("/.well-known/lnurlp/pro", headers={"x-forwarded-proto": "http"})
    body = downgraded.json()
    if "callback" in body:
        assert body["callback"].startswith("https://bitcoin-bastion.com/")


def test_dangerous_names_are_rejected_with_generic_lnurl_errors() -> None:
    client = client_for(build_service())
    for name in ("..%2Fsecret", "pro/path", "рro", "lnurlp", "callback"):
        response = client.get(f"/.well-known/lnurlp/{name}")
        body = response.json()
        assert body["status"] == "ERROR"
        assert "traceback" not in json.dumps(body).lower()
        assert response.headers["access-control-allow-origin"] == "*"


def test_raw_internal_identifiers_and_principals_are_not_exposed() -> None:
    client = client_for(build_service())
    body = client.get("/.well-known/lnurlp/pro").json()
    serialized = json.dumps(body)
    forbidden = ("database", "principal_hash", "wallet", "session", "Access Pass", "seed", "private_key")
    for value in forbidden:
        assert value not in serialized


def test_internal_exception_is_converted_to_protocol_error(monkeypatch) -> None:
    class ExplodingService:
        def resolve_address(self, address: str):
            raise RuntimeError("stack trace: private secret")

    client = client_for(build_service())
    app = client.app
    app.dependency_overrides[lnurlp.get_lightning_address_service] = lambda: ExplodingService()
    response = client.get("/.well-known/lnurlp/pro")
    assert response.json() == {"status": "ERROR", "reason": "Lightning address unavailable"}


def test_unsafe_callback_configuration_is_rejected(monkeypatch) -> None:
    base = lnurlp.LNURLPRouteConfig()
    client = client_for(build_service())
    for callback_base_url in ("http://bitcoin-bastion.com", "http://hidden.onion", "https://localhost", "https://10.0.0.1"):
        monkeypatch.setattr(lnurlp, "_config", lambda url=callback_base_url: replace(base, callback_base_url=url))
        response = client.get("/.well-known/lnurlp/pro")
        assert response.json()["status"] == "ERROR"
    monkeypatch.setattr(lnurlp, "_config", lambda: base)


def test_rate_limit_response_is_lnurl_compatible(monkeypatch) -> None:
    base = lnurlp.LNURLPRouteConfig()
    monkeypatch.setattr(lnurlp, "_config", lambda: replace(base, rate_limit_per_minute=0))
    client = client_for(build_service())
    response = client.get("/.well-known/lnurlp/pro")
    assert response.json() == {"status": "ERROR", "reason": "Payment endpoint temporarily unavailable"}
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["retry-after"] == "60"


def test_protected_bastion_api_does_not_inherit_lnurl_wildcard_cors() -> None:
    from app.main import app as main_app

    response = TestClient(main_app).get("/api/v1/public/status")
    assert response.headers.get("access-control-allow-origin") != "*"
    assert response.headers.get("access-control-allow-credentials") != "true"


def test_route_cannot_generate_arbitrary_callback_urls() -> None:
    client = client_for(build_service())
    response = client.get("/.well-known/lnurlp/pro?callback=https://attacker.example/cb")
    body = response.json()
    assert body["callback"].startswith("https://bitcoin-bastion.com/")
    assert "attacker.example" not in body["callback"]
