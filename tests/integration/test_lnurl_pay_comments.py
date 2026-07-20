from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.services.lnurl.pay.subscription_request_service import (
    InMemoryLNURLPaySubscriptionRequestRepository,
    LNURLPaySubscriptionRequestConfig,
    LNURLPaySubscriptionRequestService,
)
from app.services.lnurl.pay_callback_service import (
    InMemoryLNURLPayCallbackRepository,
    LightningInvoiceResult,
    LNURLInvoiceConflict,
    LNURLPayCallbackCommand,
    LNURLPayCallbackService,
    LNURLPayCommentNotAllowed,
)

NOW = datetime(2026, 7, 18, tzinfo=UTC)


class FakeProvider:
    provider_name = "trusted-test-provider"

    def __init__(self) -> None:
        self.calls = 0

    async def create_invoice(self, *, amount_msat: int, description_hash: str, expiry_seconds: int, idempotency_key: str, metadata: dict[str, Any]) -> LightningInvoiceResult:
        self.calls += 1
        suffix = idempotency_key[-10:]
        return LightningInvoiceResult(
            provider_invoice_id=f"inv-{suffix}",
            bolt11=f"lnbc{amount_msat}n1{suffix}",
            payment_hash=f"payment-{suffix}",
            expires_at=NOW + timedelta(seconds=expiry_seconds),
            provider_name=self.provider_name,
        )


class FakeAudit:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record_event(self, **kwargs: Any) -> Any:
        self.events.append(kwargs)

        class Event:
            event_hash = f"audit-{len(self.events)}"

        return Event()


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def create_request(comment_allowed: int | None, *, product_code: str = "pro_pass"):
    repo = InMemoryLNURLPaySubscriptionRequestRepository()
    service = LNURLPaySubscriptionRequestService(
        repository=repo,
        config=LNURLPaySubscriptionRequestConfig(public_base_url="https://pay.example.com", max_comment_length=120, comment_global_max_chars=280),
        clock=lambda: NOW,
    )
    result = service.create_subscription_request(
        plan_code="pro_pass",
        principal_hash=None,
        actor_type=None,
        product_code=product_code,
        comment_allowed=comment_allowed,
    )
    record = next(iter(repo.records.values()))
    return result, record


def test_disabled_comments_are_not_advertised_and_callback_rejects_comment() -> None:
    result, record = create_request(0)
    assert "commentAllowed" not in result.to_lnurl_response()
    callback = LNURLPayCallbackService(repository=InMemoryLNURLPayCallbackRepository({record.request_id: record}), invoice_provider=FakeProvider(), clock=lambda: NOW)

    with pytest.raises(LNURLPayCommentNotAllowed):
        run(callback.create_invoice(LNURLPayCallbackCommand(record.request_id, record.min_amount_msat, comment="Order reference 123")))


def test_payregister_comment_invoice_idempotency_and_conflict() -> None:
    result, record = create_request(120, product_code="payregister_terminal")
    assert result.to_lnurl_response()["commentAllowed"] == 120
    record = replace(record, product_code="payregister_terminal")
    provider = FakeProvider()
    audit = FakeAudit()
    repo = InMemoryLNURLPayCallbackRepository({record.request_id: record})
    callback = LNURLPayCallbackService(repository=repo, invoice_provider=provider, audit_chain=audit, clock=lambda: NOW)

    first = run(callback.create_invoice(LNURLPayCallbackCommand(record.request_id, record.min_amount_msat, comment="Order reference 123")))
    second = run(callback.create_invoice(LNURLPayCallbackCommand(record.request_id, record.min_amount_msat, comment="Order reference 123")))
    assert first.pr == second.pr
    assert provider.calls == 1
    invoice = repo.get_invoice_by_request_id(record.request_id)
    assert invoice is not None
    assert invoice.comment_hash and invoice.comment_hash.startswith("sha256:")
    assert invoice.comment_classification == "merchant_note"
    assert "Order reference 123" not in str(invoice)

    with pytest.raises(LNURLInvoiceConflict):
        run(callback.create_invoice(LNURLPayCallbackCommand(record.request_id, record.min_amount_msat, comment="Different note")))

    audit_dump = str(audit.events)
    assert "Order reference 123" not in audit_dump
    assert "comment_hash" in audit_dump


def test_comment_hash_does_not_change_product_entitlement_inputs() -> None:
    _result, record = create_request(120)
    callback = LNURLPayCallbackService(repository=InMemoryLNURLPayCallbackRepository({record.request_id: record}), invoice_provider=FakeProvider(), clock=lambda: NOW)
    invoice = run(callback.create_invoice(LNURLPayCallbackCommand(record.request_id, record.min_amount_msat, comment="receipt note only")))
    assert invoice.amount_msat == record.min_amount_msat
    persisted = callback.repository.get_invoice_by_request_id(record.request_id)
    assert persisted is not None
    assert persisted.product_code == "pro_pass"
    assert persisted.plan_code == "pro_pass"
