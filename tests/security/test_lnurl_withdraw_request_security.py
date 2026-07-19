from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

import pytest

from app.services.lnurl.encoding import decode_lnurl
from app.services.lnurl.withdraw_request_service import (
    LNURLWithdrawNotAuthorizedError,
    LNURLWithdrawPurpose,
    LNURLWithdrawRequestConfig,
    LNURLWithdrawRequestService,
    PolicyDecision,
    PrincipalContext,
)


def principal(**kw):
    data = dict(principal_type="wallet_principal", principal_reference_hash="hmac-sha256:principal", device_reference_hash="sha256:device", session_reference_hash="sha256:session")
    data.update(kw)
    return PrincipalContext(**data)


def policy(amount=50_000):
    return PolicyDecision(decision="allow", policy_hash="sha256:policy", decision_reference="sha256:decision", approved_amount_msat=amount)


def service(**cfg):
    return LNURLWithdrawRequestService(config=LNURLWithdrawRequestConfig(**{"callback_base_url": "https://bitcoin-bastion.com", "global_max_msat": 100_000, **cfg}))


def create(svc, **kw):
    args = dict(principal_context=principal(), purpose=LNURLWithdrawPurpose.SUBSCRIPTION_REFUND, approved_amount_msat=50_000, source_reference="refund-sec", policy_decision=policy())
    args.update(kw)
    return asyncio.run(svc.create_request(**args))


def raw_k1(result):
    return parse_qs(urlparse(decode_lnurl(result.lnurl).normalized_url).query)["k1"][0]


def test_unauthenticated_or_policy_missing_production_request_denied():
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), principal_context=principal(authenticated=False))
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), policy_decision=None)


def test_k1_and_callback_domain_cannot_be_client_supplied():
    svc = service()
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(svc, client_k1="a" * 64)
    result = create(svc, source_reference="refund-callback", idempotency_key="callback", client_callback_url="https://evil.example/steal")
    assert "evil.example" not in result.callback_url
    assert "bitcoin-bastion.com" in result.callback_url


def test_amount_cannot_be_increased_after_policy_approval_and_duplicate_source_blocked():
    with pytest.raises(Exception):
        create(service(), approved_amount_msat=60_000, policy_decision=policy(50_000))
    svc = service()
    create(svc, source_reference="same-source", idempotency_key="a")
    with pytest.raises(Exception):
        create(svc, source_reference="same-source", idempotency_key="b")


def test_raw_k1_and_session_token_never_logged():
    svc = service()
    result = create(svc)
    logs = repr(svc.audit_sink.events).lower()
    assert raw_k1(result) not in logs
    assert "session_token" not in logs


def test_seed_private_key_and_email_or_lightning_address_alone_cannot_authorize():
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), description="refund bitcoin_seed private_key")
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), principal_context=principal(principal_type="email", pop_session_active=False))
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), principal_context=principal(principal_type="lightning_address", pop_session_active=False))


def test_lnurl_auth_proof_alone_without_pop_policy_cannot_issue_value():
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), principal_context=principal(auth_method="lnurl_auth", pop_session_active=False))


def test_revoked_and_expired_requests_cannot_remain_usable():
    svc = service()
    result = create(svc)
    svc.revoke_request(result.withdraw_request_id, "security")
    with pytest.raises(Exception):
        svc.validate_request_usable_for_callback(result.withdraw_request_id)
    result2 = create(svc, source_reference="expire-source", idempotency_key="expire")
    svc.expire_request(result2.withdraw_request_id)
    with pytest.raises(Exception):
        svc.validate_request_usable_for_callback(result2.withdraw_request_id)


def test_malformed_purpose_metadata_fails_safely():
    with pytest.raises(LNURLWithdrawNotAuthorizedError):
        create(service(), purpose="../../pay")
