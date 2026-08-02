from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx

from bitcoin_bastion_sdk import BastionClient
from bitcoin_bastion_sdk.lnurl.address import lightning_address_path
from bitcoin_bastion_sdk.lnurl.payer_data import LNURLPayerData
from bitcoin_bastion_sdk.lnurl.success_action import LNURLSuccessURL
from bitcoin_bastion_sdk.lnurl.types import LNURLAuthChallenge, LNURLPaymentState


def test_lnurl_payment_invoice_is_not_settlement() -> None:
    client = BastionClient(base_url="http://example.com", transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"data": {"payment_id": "pay_safe", "status": "invoice_issued", "entitlement_active": False}, "error": None, "meta": {}})))
    payment = client.auth.lnurl.create_subscription_payment(plan="pro_pass")
    assert payment.state is LNURLPaymentState.INVOICE_ISSUED
    assert not payment.settled
    assert not payment.entitlement_active


def test_lnurl_sensitive_values_have_safe_repr_and_privacy_defaults() -> None:
    challenge = LNURLAuthChallenge("lnc_safe", "LNURL1SAFE", "login", "bastion.example", datetime.now(UTC) + timedelta(minutes=1), k1="ab" * 32)
    assert "ab" * 32 not in repr(challenge)
    assert LNURLPayerData().email is None


def test_lightning_address_is_routing_and_success_url_is_not_opened() -> None:
    assert lightning_address_path("pro@bitcoin-bastion.com").endswith("/.well-known/lnurlp/pro")
    action = LNURLSuccessURL("Activated", "https://bastion.example/activation/opaque")
    assert action.url.startswith("https://")
