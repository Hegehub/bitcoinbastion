from __future__ import annotations

import asyncio
import threading
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from app.services.lnurl.encoding import decode_lnurl
from app.services.lnurl.k1_registry import LNURLK1Status
from app.services.lnurl.repositories.withdraw_requests import LNURLWithdrawRequestStatus
from app.services.lnurl.withdraw_request_service import (
    InMemoryLNURLWithdrawAuditSink,
    LNURLWithdrawIdempotencyConflictError,
    LNURLWithdrawInvalidAmountError,
    LNURLWithdrawLimitExceededError,
    LNURLWithdrawNotAuthorizedError,
    LNURLWithdrawPurpose,
    LNURLWithdrawRequestConfig,
    LNURLWithdrawRequestService,
    LNURLWithdrawSourceAlreadyConsumedError,
    LNURLWithdrawSourceRequiredError,
    LNURLWithdrawStepUpRequiredError,
    PolicyDecision,
    PrincipalContext,
)


def principal(**kw) -> PrincipalContext:
    base = dict(
        principal_type="wallet_principal",
        principal_reference_hash="hmac-sha256:principal",
        device_reference_hash="sha256:device",
        session_reference_hash="sha256:session",
    )
    base.update(kw)
    return PrincipalContext(**base)


def policy(amount: int = 50_000, decision: str = "allow") -> PolicyDecision:
    return PolicyDecision(decision=decision, policy_hash="sha256:policy", decision_reference="sha256:decision", approved_amount_msat=amount, required_step_up="fresh_wallet_proof" if decision == "step_up_required" else None)


def service(**cfg) -> LNURLWithdrawRequestService:
    config = LNURLWithdrawRequestConfig(**{"callback_base_url": "https://bitcoin-bastion.com", "global_max_msat": 100_000, **cfg})
    return LNURLWithdrawRequestService(config=config, audit_sink=InMemoryLNURLWithdrawAuditSink())


def create(svc: LNURLWithdrawRequestService, **kw):
    kwargs = dict(principal_context=principal(), purpose=LNURLWithdrawPurpose.SUBSCRIPTION_REFUND, approved_amount_msat=50_000, source_reference="refund-case-1", policy_decision=policy())
    kwargs.update(kw)
    return asyncio.run(svc.create_request(**kwargs))


def raw_k1_from_lnurl(result) -> str:
    decoded = decode_lnurl(result.lnurl).normalized_url
    return parse_qs(urlparse(decoded).query)["k1"][0]


def test_valid_authorized_request_is_created_and_contract_fields_roundtrip():
    svc = service()
    result = create(svc)
    assert result.tag == "withdrawRequest"
    assert result.status == LNURLWithdrawRequestStatus.LNURL_ISSUED.value
    assert result.min_withdrawable_msat == result.max_withdrawable_msat == 50_000
    assert result.callback_url.startswith("https://bitcoin-bastion.com/v1/lnurl/withdraw/callback/wdr_")
    k1 = raw_k1_from_lnurl(result)
    assert len(k1) == 64
    assert bytes.fromhex(k1)
    assert decode_lnurl(result.lnurl).normalized_url == f"{result.callback_url}?k1={k1}"


def test_two_requests_receive_different_k1_and_raw_k1_not_persisted():
    svc = service()
    first = create(svc, source_reference="refund-1", idempotency_key="one")
    second = create(svc, source_reference="refund-2", idempotency_key="two")
    assert raw_k1_from_lnurl(first) != raw_k1_from_lnurl(second)
    record = svc.repository.get_by_request_id(first.withdraw_request_id)
    stored = repr(record).lower()
    assert raw_k1_from_lnurl(first) not in stored
    assert "k1_lookup_hash" not in stored


def test_invalid_amount_bounds_and_limits_are_rejected():
    svc = service()
    with pytest.raises(LNURLWithdrawInvalidAmountError):
        create(svc, approved_amount_msat=0, policy_decision=policy(0))
    with pytest.raises(LNURLWithdrawInvalidAmountError):
        create(svc, min_withdrawable_msat=20_000, max_withdrawable_msat=10_000)
    with pytest.raises(LNURLWithdrawLimitExceededError):
        create(svc, approved_amount_msat=60_000, policy_decision=policy(50_000))
    with pytest.raises(LNURLWithdrawLimitExceededError):
        create(service(global_max_msat=10_000), approved_amount_msat=50_000, policy_decision=policy(50_000))


def test_missing_source_required_for_refund_and_duplicate_source_blocked():
    svc = service()
    with pytest.raises(LNURLWithdrawSourceRequiredError):
        create(svc, source_reference=None)
    create(svc, source_reference="refund-dup", idempotency_key="a")
    with pytest.raises(LNURLWithdrawSourceAlreadyConsumedError):
        create(svc, source_reference="refund-dup", idempotency_key="b")


def test_callback_url_server_controlled_and_client_callback_ignored():
    svc = service()
    result = create(svc, client_callback_url="https://attacker.example/callback")
    assert "attacker.example" not in result.callback_url
    assert any(event["event_type"] == "lnurl_withdraw_client_callback_ignored" for event in svc.audit_sink.events)


def test_description_sanitized_and_secret_terms_rejected():
    result = create(service(), description="<b>Bitcoin Bastion refund</b>\n")
    assert "<" not in result.default_description
    assert "\n" not in result.default_description
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), description="refund session token abc")


def test_expiry_uses_short_ttl_and_caps_excessive_requested_ttl():
    svc = service(default_ttl_seconds=300, max_ttl_seconds=600)
    before = datetime.now(UTC)
    result = create(svc, expires_in_seconds=9999)
    assert before + timedelta(seconds=590) <= result.expires_at <= before + timedelta(seconds=610)


def test_idempotent_duplicate_same_payload_returns_same_active_request_and_conflict_fails():
    svc = service()
    first = create(svc, idempotency_key="idem", source_reference="refund-idem")
    second = create(svc, idempotency_key="idem", source_reference="refund-idem")
    assert second.withdraw_request_id == first.withdraw_request_id
    with pytest.raises(LNURLWithdrawIdempotencyConflictError):
        create(svc, idempotency_key="idem", source_reference="refund-idem", approved_amount_msat=40_000, policy_decision=policy(40_000))


def test_policy_deny_step_up_revoked_principal_device_and_expired_session_rejected():
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), policy_decision=policy(decision="deny"))
    with pytest.raises(LNURLWithdrawStepUpRequiredError):
        create(service(), policy_decision=policy(decision="step_up_required"))
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), principal_context=principal(principal_active=False))
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), principal_context=principal(device_active=False))
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), principal_context=principal(session_active=False))


def test_request_creation_emits_audit_without_raw_k1_or_session_token():
    svc = service()
    result = create(svc)
    assert [e["event_type"] for e in svc.audit_sink.events if e["event_type"].startswith("lnurl_withdraw_request_")] == ["lnurl_withdraw_request_created", "lnurl_withdraw_request_issued"]
    audit_text = repr(svc.audit_sink.events).lower()
    assert raw_k1_from_lnurl(result) not in audit_text
    assert "session_token" not in audit_text


def test_mainnet_test_faucet_and_unknown_purpose_denied():
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(require_policy=False), purpose=LNURLWithdrawPurpose.TESTNET_FAUCET, source_reference=None, policy_decision=None)
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), purpose="unknown")


def test_revoke_cancel_expire_and_callback_state_queries():
    svc = service()
    result = create(svc)
    assert svc.validate_request_usable_for_callback(result.withdraw_request_id).status == LNURLWithdrawRequestStatus.LNURL_ISSUED
    revoked = svc.revoke_request(result.withdraw_request_id, "operator_revoked")
    assert revoked.status == LNURLWithdrawRequestStatus.REVOKED
    k1_record = svc.k1_registry.get_k1_status_by_registry_id(revoked.k1_registry_id)
    assert k1_record and k1_record.status == LNURLK1Status.REVOKED
    result2 = create(svc, source_reference="refund-expire", idempotency_key="expire")
    expired = svc.expire_request(result2.withdraw_request_id)
    assert expired.status == LNURLWithdrawRequestStatus.EXPIRED


def test_concurrent_same_idempotency_key_returns_one_request():
    svc = service()
    results = []
    def worker():
        results.append(create(svc, idempotency_key="concurrent", source_reference="refund-concurrent"))
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len({r.withdraw_request_id for r in results}) == 1
