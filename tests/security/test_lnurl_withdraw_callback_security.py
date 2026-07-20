from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse
from dataclasses import replace

from fastapi.testclient import TestClient

from app.main import app
from app.services.lnurl.encoding import decode_lnurl
from app.services.lnurl.repositories.withdraw_requests import LNURLWithdrawRequestStatus
from app.services.lnurl.url_safety import LNURLURLPolicy
from app.services.lnurl.verification_sources import test_bolt11 as make_test_bolt11
from app.services.lnurl.withdraw_callback_verifier import InMemorySensitiveInvoiceStore, LNURLWithdrawCallbackVerifier, LNURLWithdrawCallbackVerifierConfig
from app.services.lnurl.withdraw_request_service import LNURLWithdrawPurpose, LNURLWithdrawRequestConfig, LNURLWithdrawRequestService, PolicyDecision, PrincipalContext


def _ctx(**overrides):
    values = dict(
        principal_type="lightning_wallet_principal",
        principal_reference_hash="hmac-sha256:principal",
        device_reference_hash="sha256:device",
        session_reference_hash="sha256:session",
        business_role="cashier",
        workspace_hash="hmac-sha256:workspace",
    )
    values.update(overrides)
    return PrincipalContext(**values)


def _policy(amount=50_000):
    return PolicyDecision("allow", "sha256:policy", "decision:1", amount)


async def _fixture(amount=50_000):
    svc = LNURLWithdrawRequestService(config=LNURLWithdrawRequestConfig(enabled=True))
    res = await svc.create_request(principal_context=_ctx(), purpose=LNURLWithdrawPurpose.SUBSCRIPTION_REFUND, approved_amount_msat=amount, source_reference="source:one", policy_decision=_policy(amount))
    decoded = decode_lnurl(res.lnurl, policy=LNURLURLPolicy.service_owned_callback(domains={"bitcoin-bastion.com"}))
    k1 = parse_qs(urlparse(decoded.normalized_url).query)["k1"][0]
    verifier = LNURLWithdrawCallbackVerifier(request_service=svc, invoice_store=InMemorySensitiveInvoiceStore(), config=LNURLWithdrawCallbackVerifierConfig(server_pepper=svc.config.server_pepper, require_protected_invoice_store=False))
    return svc, verifier, res.withdraw_request_id, k1


def _invoice(amount=50_000, payment_hash="a" * 64):
    return make_test_bolt11(payment_hash=payment_hash, amount_msat=amount, network="bitcoin-mainnet")


def test_callback_cannot_change_authorized_amount_principal_role_or_store() -> None:
    async def run():
        svc, verifier, withdraw_id, k1 = await _fixture(amount=50_000)
        inflated = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=_invoice(amount=75_000))
        assert inflated.accepted is False
        accepted = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=_invoice())
        assert accepted.accepted is True
        record = svc.repository.get_by_request_id(withdraw_id)
        assert record is not None
        assert record.principal_reference_hash == "hmac-sha256:principal"
        assert record.metadata_json is None or "workspace" not in repr(record.metadata_json).lower()
    asyncio.run(run())


def test_k1_single_use_replay_and_invoice_substitution_rejected() -> None:
    async def run():
        _, verifier, withdraw_id, k1 = await _fixture()
        invoice = _invoice(payment_hash="b" * 64)
        first = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=invoice)
        replay = await verifier.verify_callback(withdraw_id=withdraw_id, k1="f" * 64, pr=invoice)
        substitution = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=_invoice(payment_hash="c" * 64))
        assert first.accepted is True
        assert replay.accepted is False
        assert substitution.accepted is False
    asyncio.run(run())


def test_callback_does_not_trigger_payment_auth_session_or_private_key_acceptance() -> None:
    async def run():
        svc, verifier, withdraw_id, k1 = await _fixture()
        pr = _invoice(payment_hash="d" * 64)
        result = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=pr)
        assert result.accepted is True
        events = repr(svc.audit_sink.events).lower()
        assert "paid" not in events
        assert "session_created" not in events
        assert "private key" not in events
        assert "wallet seed" not in events
    asyncio.run(run())


def test_malformed_oversized_invoice_rejected_before_expensive_processing() -> None:
    async def run():
        _, verifier, withdraw_id, k1 = await _fixture()
        result = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr="lnbc" + "x" * 5000)
        assert result.accepted is False
        assert result.verification_reason_code == "invoice_too_large"
    asyncio.run(run())


def test_wildcard_cors_limited_to_lnurl_endpoint() -> None:
    client = TestClient(app)
    lnurl = client.get("/v1/lnurl/withdraw/callback/wdr_missing?k1=" + "a" * 64 + "&pr=bad")
    health = client.get("/health")
    assert lnurl.headers.get("access-control-allow-origin") == "*"
    assert health.headers.get("access-control-allow-origin") != "*"


def test_callback_cannot_bypass_preauthorization_state() -> None:
    async def run():
        svc, verifier, withdraw_id, k1 = await _fixture()
        record = svc.repository.get_by_request_id(withdraw_id)
        assert record is not None
        svc.repository.update(replace(record, status=LNURLWithdrawRequestStatus.CANCELLED))
        result = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=_invoice())
        assert result.accepted is False
    asyncio.run(run())
