from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app


def test_product_address_route_returns_fixed_price_canonical_pay_request() -> None:
    body = TestClient(app, headers={"host": "bitcoin-bastion.com"}).get("/.well-known/lnurlp/pro").json()
    assert body["tag"] == "payRequest"
    assert body["minSendable"] == body["maxSendable"] == 500_000_000
    metadata = json.loads(body["metadata"])
    assert metadata == [
        ["text/plain", "Bitcoin Bastion Pro Pass — 1 month"],
        ["text/long-desc", "Advanced signals, historical similarity, automation and professional API access."],
        ["text/identifier", "pro@bitcoin-bastion.com"],
    ]
    assert body["payerData"]["auth"]["mandatory"] is False
    assert "commentAllowed" not in body
    assert body["callback"].startswith("https://bitcoin-bastion.com/api/v1/lnurl/pay/callback/")


def test_all_public_products_resolve_and_enterprise_is_unavailable() -> None:
    client = TestClient(app, headers={"host": "bitcoin-bastion.com"})
    expected = {"lite": "lite_pass", "basic": "basic_pass", "plus": "plus_pass", "pro": "pro_pass", "business": "business_pass"}
    for name in expected:
        body = client.get(f"/.well-known/lnurlp/{name}").json()
        assert body["tag"] == "payRequest"
        assert f"{name}@bitcoin-bastion.com" in body["metadata"]
        assert "principal" not in json.dumps(body).lower()
    enterprise = client.get("/.well-known/lnurlp/enterprise").json()
    assert enterprise == {"status": "ERROR", "reason": "Lightning address unavailable"}
