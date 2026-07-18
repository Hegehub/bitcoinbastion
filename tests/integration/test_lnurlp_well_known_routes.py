from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.well_known import lnurlp
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.lnurl.lightning_address_service import LightningAddressService, LightningAddressServiceConfig


def build_service() -> LightningAddressService:
    service = LightningAddressService(config=LightningAddressServiceConfig(primary_domain="bitcoin-bastion.com"))
    service.create_product_address(local_part="pro")
    service.create_merchant_address(
        local_part="merchant-1",
        domain="bitcoin-bastion.com",
        merchant_reference_hash=sha256_prefixed("merchant-db-id"),
        display_label="Merchant One",
    )
    suspended = service.create_product_address(local_part="lite")
    service.suspend_address(suspended.address_id)
    return service


def client_for(service: LightningAddressService) -> TestClient:
    lnurlp._RATE_BUCKETS.clear()
    app = FastAPI()
    app.include_router(lnurlp.router)
    app.dependency_overrides[lnurlp.get_lightning_address_service] = lambda: service
    return TestClient(app, headers={"host": "bitcoin-bastion.com"})


def assert_pay_request(body: dict) -> list[list[str]]:
    assert body["tag"] == "payRequest"
    assert isinstance(body["minSendable"], int)
    assert isinstance(body["maxSendable"], int)
    assert body["minSendable"] >= 1
    assert body["maxSendable"] >= body["minSendable"]
    assert body["callback"].startswith("https://bitcoin-bastion.com/api/v1/lnurl/pay/callback/")
    metadata = json.loads(body["metadata"])
    assert any(item[0] == "text/plain" for item in metadata)
    assert any(item[0] == "text/identifier" for item in metadata)
    assert "data" not in body
    assert "success" not in body
    return metadata


def test_valid_product_alias_returns_raw_lnurl_pay_request() -> None:
    client = client_for(build_service())
    response = client.get("/.well-known/lnurlp/pro")
    body = response.json()
    metadata = assert_pay_request(body)
    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in response.headers
    assert response.headers["cache-control"] == "no-store"
    assert any(item == ["text/identifier", "pro@bitcoin-bastion.com"] for item in metadata)


def test_valid_merchant_alias_returns_pay_request_without_internal_ids() -> None:
    client = client_for(build_service())
    response = client.get("/.well-known/lnurlp/merchant-1")
    body = response.json()
    assert_pay_request(body)
    serialized = json.dumps(body)
    assert "merchant-db-id" not in serialized
    assert "principal" not in serialized.lower()


def test_unknown_suspended_and_invalid_aliases_return_lnurl_error_json() -> None:
    client = client_for(build_service())
    for path in ("unknown", "lite", "..%2Fx", "admin"):
        response = client.get(f"/.well-known/lnurlp/{path}")
        body = response.json()
        assert body["status"] == "ERROR"
        assert "reason" in body
        assert response.headers["access-control-allow-origin"] == "*"
        assert "data" not in body


def test_head_and_options_are_read_only_and_public() -> None:
    service = build_service()
    client = client_for(service)
    head = client.head("/.well-known/lnurlp/pro")
    options = client.options("/.well-known/lnurlp/pro")
    assert head.status_code == 200
    assert head.text == ""
    assert head.headers["access-control-allow-origin"] == "*"
    assert options.status_code == 204
    assert "GET" in options.headers["allow"]
    assert service.pay_request_service.repository.count_invoices() == 0
    assert service.pay_request_service.repository.count_entitlements() == 0


def test_discovery_route_requires_no_pop_session_and_does_not_issue_invoice_or_entitlement() -> None:
    service = build_service()
    client = client_for(service)
    response = client.get("/.well-known/lnurlp/pro")
    assert response.status_code == 200
    assert response.json()["tag"] == "payRequest"
    assert service.pay_request_service.repository.count_invoices() == 0
    assert service.pay_request_service.repository.count_entitlements() == 0
