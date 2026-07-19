from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from app.services.access.crypto.hashing import sha256_prefixed
from app.services.lnurl.encoding import decode_lnurl
from app.services.lnurl.repositories.withdraw_requests import LNURLWithdrawRequestStatus
from app.services.lnurl.url_safety import LNURLURLPolicy
from app.services.lnurl.verification_sources import test_bolt11 as make_test_bolt11
from app.services.lnurl.withdraw_callback_verifier import (
    InMemorySensitiveInvoiceStore,
    LNURLWithdrawCallbackVerifier,
    LNURLWithdrawCallbackVerifierConfig,
)
from app.services.lnurl.withdraw_request_service import (
    LNURLWithdrawPurpose,
    LNURLWithdrawRequestConfig,
    LNURLWithdrawRequestService,
    PolicyDecision,
    PrincipalContext,
)


def _ctx() -> PrincipalContext:
    return PrincipalContext(
        principal_type="lightning_wallet_principal",
        principal_reference_hash="hmac-sha256:principal",
        device_reference_hash="sha256:device",
        session_reference_hash="sha256:session",
    )


def _policy(amount: int) -> PolicyDecision:
    return PolicyDecision("allow", "sha256:policy", "decision:1", amount)


async def _request(amount: int = 50_000, network: str = "bitcoin-mainnet"):
    svc = LNURLWithdrawRequestService(config=LNURLWithdrawRequestConfig(enabled=True, network=network))
    result = await svc.create_request(
        principal_context=_ctx(),
        purpose=LNURLWithdrawPurpose.SUBSCRIPTION_REFUND,
        approved_amount_msat=amount,
        source_reference="subscription_payment_id_hash:one",
        policy_decision=_policy(amount),
    )
    decoded = decode_lnurl(result.lnurl, policy=LNURLURLPolicy.service_owned_callback(domains={"bitcoin-bastion.com"}))
    k1 = parse_qs(urlparse(decoded.normalized_url).query)["k1"][0]
    verifier = LNURLWithdrawCallbackVerifier(
        request_service=svc,
        invoice_store=InMemorySensitiveInvoiceStore(),
        config=LNURLWithdrawCallbackVerifierConfig(server_pepper=svc.config.server_pepper, require_protected_invoice_store=False),
    )
    return svc, verifier, result.withdraw_request_id, k1


def _invoice(amount: int = 50_000, network: str = "bitcoin-mainnet", *, payment_hash: str = "a" * 64, seconds: int = 900) -> str:
    return make_test_bolt11(payment_hash=payment_hash, amount_msat=amount, network=network, timestamp=datetime.now(UTC), expiry_seconds=seconds)


def test_valid_callback_is_accepted_and_does_not_pay_invoice() -> None:
    async def run():
        svc, verifier, withdraw_id, k1 = await _request()
        result = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=_invoice())
        assert result.accepted is True
        assert result.status == LNURLWithdrawRequestStatus.INVOICE_RECEIVED.value
        assert result.policy_evaluation_required is True
        record = svc.repository.get_by_request_id(withdraw_id)
        assert record is not None
        assert record.status == LNURLWithdrawRequestStatus.INVOICE_RECEIVED
        assert record.invoice_hash is not None
        assert record.payment_hash_hash is not None
        assert record.invoice_store_reference is not None
        assert not any(e["event_type"].endswith("paid") for e in svc.audit_sink.events)
    asyncio.run(run())


@pytest.mark.parametrize(
    ("k1", "reason"),
    [("bad", "k1_invalid_format"), ("f" * 64, "k1_mismatch")],
)
def test_invalid_or_wrong_k1_rejected(k1: str, reason: str) -> None:
    async def run():
        _, verifier, withdraw_id, _ = await _request()
        result = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=_invoice())
        assert result.accepted is False
        assert result.verification_reason_code == reason
    asyncio.run(run())


def test_expired_withdraw_and_revoked_withdraw_rejected() -> None:
    async def run():
        svc, verifier, withdraw_id, k1 = await _request()
        svc.expire_request(withdraw_id)
        expired = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=_invoice())
        assert expired.accepted is False
        assert expired.verification_reason_code == "withdraw_expired"
        svc2, verifier2, withdraw_id2, k12 = await _request()
        svc2.revoke_request(withdraw_id2, "security")
        revoked = await verifier2.verify_callback(withdraw_id=withdraw_id2, k1=k12, pr=_invoice(payment_hash="b" * 64))
        assert revoked.accepted is False
        assert revoked.verification_reason_code == "withdraw_revoked"
    asyncio.run(run())


@pytest.mark.parametrize(
    ("invoice", "reason"),
    [
        ("not-a-bolt11", "invoice_decode_failed"),
        (_invoice(network="bitcoin-testnet"), "invoice_network_mismatch"),
        (_invoice(amount=1), "invoice_amount_below_minimum"),
        (_invoice(amount=100_000), "invoice_amount_above_maximum"),
        (_invoice(seconds=60), "invoice_ttl_too_short"),
        (make_test_bolt11(payment_hash="c" * 64, amount_msat=50_000, network="bitcoin-mainnet", timestamp=datetime.now(UTC) - timedelta(hours=1), expiry_seconds=60), "invoice_expired"),
    ],
)
def test_invoice_validation_rejections(invoice: str, reason: str) -> None:
    async def run():
        _, verifier, withdraw_id, k1 = await _request()
        result = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=invoice)
        assert result.accepted is False
        assert result.verification_reason_code == reason
    asyncio.run(run())


def test_amountless_invoice_rejected_by_default() -> None:
    async def run():
        _, verifier, withdraw_id, k1 = await _request()
        # Explicit test fixture for an amountless invoice; production-looking
        # invoices are still decoded through the project decoder abstraction.
        pr = "testbolt11:eyJwYXltZW50X2hhc2giOiJkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZCIsImFtb3VudF9tc2F0IjpudWxsLCJuZXR3b3JrIjoiYml0Y29pbi1tYWlubmV0IiwidGltZXN0YW1wIjozMDAwMDAwMDAwLCJleHBpcnlfc2Vjb25kcyI6OTAwfQ"
        result = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=pr)
        assert result.accepted is False
        assert result.verification_reason_code == "invoice_amount_missing"
    asyncio.run(run())


def test_duplicate_same_callback_idempotent_and_substitution_rejected() -> None:
    async def run():
        _, verifier, withdraw_id, k1 = await _request()
        invoice = _invoice(payment_hash="e" * 64)
        first = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=invoice)
        second = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=invoice)
        changed = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=_invoice(payment_hash="f" * 64))
        assert first.accepted is True
        assert second.accepted is True
        assert second.verification_reason_code == "duplicate_callback_accepted"
        assert changed.accepted is False
    asyncio.run(run())


def test_duplicate_invoice_and_payment_hash_across_requests_rejected() -> None:
    async def run():
        svc, verifier1, withdraw_id1, k11 = await _request()
        invoice = _invoice(payment_hash="1" * 64)
        assert (await verifier1.verify_callback(withdraw_id=withdraw_id1, k1=k11, pr=invoice)).accepted
        result2 = await svc.create_request(principal_context=_ctx(), purpose=LNURLWithdrawPurpose.SUBSCRIPTION_REFUND, approved_amount_msat=50_000, source_reference="subscription_payment_id_hash:two", policy_decision=_policy(50_000))
        decoded = decode_lnurl(result2.lnurl, policy=LNURLURLPolicy.service_owned_callback(domains={"bitcoin-bastion.com"}))
        k12 = parse_qs(urlparse(decoded.normalized_url).query)["k1"][0]
        result = await verifier1.verify_callback(withdraw_id=result2.withdraw_request_id, k1=k12, pr=invoice)
        assert result.accepted is False
        assert result.verification_reason_code in {"invoice_duplicate", "payment_hash_duplicate"}
    asyncio.run(run())


def test_concurrent_callback_creates_one_invoice_attachment() -> None:
    async def run():
        svc, verifier, withdraw_id, k1 = await _request()
        invoice = _invoice(payment_hash="2" * 64)
        results = await asyncio.gather(*[verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=invoice) for _ in range(4)])
        assert any(result.accepted for result in results)
        record = svc.repository.get_by_request_id(withdraw_id)
        assert record is not None and record.invoice_hash == sha256_prefixed(invoice)
        handoffs = [e for e in svc.audit_sink.events if e["event_type"] == "lnurl_withdraw_policy_handoff_created"]
        assert len(handoffs) == 1
    asyncio.run(run())


def test_audit_events_redact_raw_k1_invoice_and_payment_hash() -> None:
    async def run():
        svc, verifier, withdraw_id, k1 = await _request()
        invoice = _invoice(payment_hash="3" * 64)
        await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=invoice)
        events = repr(svc.audit_sink.events)
        assert k1 not in events
        assert invoice not in events
        assert "3" * 64 not in events
        assert "invoice_hash" in events
    asyncio.run(run())
