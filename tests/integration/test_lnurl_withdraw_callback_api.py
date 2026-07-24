from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

import app.api.v1.lnurl as lnurl_api
from app.main import app
from app.services.lnurl.encoding import decode_lnurl
from app.services.lnurl.url_safety import LNURLURLPolicy
from app.services.lnurl.verification_sources import test_bolt11 as make_test_bolt11
from app.services.lnurl.withdraw_callback_verifier import InMemorySensitiveInvoiceStore, LNURLWithdrawCallbackVerifier, LNURLWithdrawCallbackVerifierConfig
from app.services.lnurl.withdraw_request_service import LNURLWithdrawPurpose, LNURLWithdrawRequestConfig, LNURLWithdrawRequestService, PolicyDecision, PrincipalContext


def test_lnurl_withdraw_callback_api_flow() -> None:
    async def setup():
        svc = LNURLWithdrawRequestService(config=LNURLWithdrawRequestConfig(enabled=True))
        verifier = LNURLWithdrawCallbackVerifier(request_service=svc, invoice_store=InMemorySensitiveInvoiceStore(), config=LNURLWithdrawCallbackVerifierConfig(server_pepper=svc.config.server_pepper, require_protected_invoice_store=False))
        lnurl_api._DEFAULT_WITHDRAW_CALLBACK_VERIFIER = verifier
        lnurl_api._DEFAULT_WITHDRAW_REQUEST_SERVICE = svc
        res = await svc.create_request(
            principal_context=PrincipalContext("lightning_wallet_principal", "hmac-sha256:principal", "sha256:device", "sha256:session"),
            purpose=LNURLWithdrawPurpose.SUBSCRIPTION_REFUND,
            approved_amount_msat=50_000,
            source_reference="source:api",
            policy_decision=PolicyDecision("allow", "sha256:policy", "decision:api", 50_000),
        )
        decoded = decode_lnurl(res.lnurl, policy=LNURLURLPolicy.service_owned_callback(domains={"bitcoin-bastion.com"}))
        return svc, res.withdraw_request_id, parse_qs(urlparse(decoded.normalized_url).query)["k1"][0]
    svc, withdraw_id, k1 = asyncio.run(setup())
    invoice = make_test_bolt11(payment_hash="9" * 64, amount_msat=50_000, network="bitcoin-mainnet")
    client = TestClient(app)
    first = client.get(f"/v1/lnurl/withdraw/callback/{withdraw_id}", params={"k1": k1, "pr": invoice})
    assert first.status_code == 200
    assert first.json() == {"status": "OK"}
    record = svc.repository.get_by_request_id(withdraw_id)
    assert record is not None
    assert record.status.value == "invoice_received"
    assert record.payment_hash_hash is not None
    assert record.invoice_hash is not None
    assert record.policy_handoff_id is not None
    assert svc.k1_registry.get_k1_status(k1).status.value == "consumed"
    assert any(e["event_type"] == "lnurl_withdraw_policy_handoff_created" for e in svc.audit_sink.events)
    assert not any("paid" in e["event_type"] for e in svc.audit_sink.events)
    second = client.get(f"/v1/lnurl/withdraw/callback/{withdraw_id}", params={"k1": k1, "pr": invoice})
    assert second.json() == {"status": "OK"}
    modified = make_test_bolt11(payment_hash="8" * 64, amount_msat=50_000, network="bitcoin-mainnet")
    rejected = client.get(f"/v1/lnurl/withdraw/callback/{withdraw_id}", params={"k1": k1, "pr": modified})
    assert rejected.json()["status"] == "ERROR"
