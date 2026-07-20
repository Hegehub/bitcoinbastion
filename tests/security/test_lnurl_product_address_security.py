from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.lnurl.product_addresses import ProductAddressConfigError, validate_product_address_name


def test_product_lightning_address_is_not_identity_or_authorization() -> None:
    body = TestClient(app, headers={"host": "bitcoin-bastion.com"}).get("/.well-known/lnurlp/pro").json()
    serialized = json.dumps(body).lower()
    assert body["tag"] == "payRequest"
    assert "user_id" not in serialized
    assert "principal_hash" not in serialized
    assert "session" not in serialized
    assert "access pass" not in serialized
    assert "entitlement" not in serialized


def test_product_input_attacks_return_safe_errors() -> None:
    client = TestClient(app, headers={"host": "bitcoin-bastion.com"})
    for name in ("..%2Fpro", "pro/annual", "рro", "business%20admin"):
        body = client.get(f"/.well-known/lnurlp/{name}").json()
        assert body["status"] == "ERROR"
        assert "traceback" not in json.dumps(body).lower()
    for raw in ("../pro", "%2e%2e/pro", "Pro", "pro@example", "pro/annual", "рro", "business admin"):
        with pytest.raises(ProductAddressConfigError):
            validate_product_address_name(raw)


def test_comments_payerdata_and_amount_cannot_select_plan_or_roles() -> None:
    body = TestClient(app, headers={"host": "bitcoin-bastion.com"}).get("/.well-known/lnurlp/basic?plan=enterprise_pass&amount=1&role=owner").json()
    assert body["tag"] == "payRequest"
    assert body["minSendable"] == body["maxSendable"] == 50_000_000
    assert "enterprise_pass" not in body["metadata"]
    assert "owner" not in body["metadata"].lower()
    assert body["payerData"]["auth"]["mandatory"] is False
    assert "email" not in json.dumps(body["payerData"]).lower()
    assert "name" not in json.dumps(body["payerData"]).lower()


def test_business_and_enterprise_do_not_create_owner_or_contract_authority() -> None:
    client = TestClient(app, headers={"host": "bitcoin-bastion.com"})
    business = client.get("/.well-known/lnurlp/business").json()
    assert business["tag"] == "payRequest"
    assert "owner" not in json.dumps(business).lower()
    enterprise = client.get("/.well-known/lnurlp/enterprise").json()
    assert enterprise == {"status": "ERROR", "reason": "Lightning address unavailable"}
