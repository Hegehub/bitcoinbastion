from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from app.services.lnurl.pay_callback_service import LNURLPayCallbackCommand, LNURLPayCommentNotAllowed, LNURLPayerDataInvalid
from app.services.lnurl.pay.errors import LNURLPayInvalidAmountError, LNURLPayRequestError
from tests.unit.test_lnurl_pay_callback_service import FakeProvider, request_record, service

NOW = datetime(2026, 7, 17, tzinfo=UTC)


def run(coro):
    return asyncio.run(coro)


def test_callback_cannot_lower_subscription_price_or_select_higher_plan() -> None:
    svc, _, provider, _ = service(request_record())

    with pytest.raises(LNURLPayInvalidAmountError):
        run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 99_999, client_context={"plan_code": "lite_pass"})))

    assert provider.calls == []


def test_comment_and_payerdata_cannot_authorize_access() -> None:
    comment_svc, _, _, _ = service(request_record(comment_allowed=64))
    with pytest.raises(LNURLPayCommentNotAllowed):
        run(comment_svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, comment="grants access to admin")))

    payer_svc, repo, _, _ = service(request_record(payer_data_policy={"auth": {"mandatory": False}}))
    result = run(payer_svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, payer_data={"auth": {"proof": "pending"}})))
    assert result.payment_status == "invoice_issued"
    assert repo.count_entitlements() == 0

    bad, _, _, _ = service(request_record(payer_data_policy={"auth": {"mandatory": False}}))
    with pytest.raises(LNURLPayerDataInvalid):
        run(bad.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, payer_data={"email": "person@example.com"})))


def test_raw_provider_secrets_and_payerdata_are_not_logged_or_audited() -> None:
    svc, _, provider, audit = service(request_record(payer_data_policy={"auth": {"mandatory": False}}), provider=FakeProvider())

    run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, payer_data={"auth": {"k1_hash": "sha256:safe"}})))
    serialized = str(audit.events).lower() + str(provider.calls).lower()

    assert "person@example.com" not in serialized
    assert "provider_secret" not in serialized
    assert "preimage" not in serialized
    assert "private_key" not in serialized
    assert "payer_data" not in serialized


def test_no_seed_or_private_key_input_path_exists() -> None:
    svc, _, _, _ = service(request_record())

    with pytest.raises(LNURLPayRequestError):
        run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, client_context={"bitcoin_seed": "seed phrase words"})))


def test_duplicate_callback_cannot_create_invoice_storm() -> None:
    svc, _, provider, _ = service(request_record())

    first = run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)))
    for _ in range(5):
        assert run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000))).pr == first.pr

    assert len(provider.calls) == 1
