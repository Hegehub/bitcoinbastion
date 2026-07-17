from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.services.lnurl.pay.subscription_request_service import LNURLPayRequestRecord, LNURLPayRequestStatus
from app.services.lnurl.pay_callback_service import (
    InMemoryLNURLPayCallbackRepository,
    LightningInvoiceResult,
    LNURLInvoiceConflict,
    LNURLInvoiceCreationFailed,
    LNURLInvoiceProviderUnavailable,
    LNURLPayCallbackCommand,
    LNURLPayCallbackConfig,
    LNURLPayCallbackService,
    LNURLPayCommentNotAllowed,
    LNURLPayCommentTooLong,
    LNURLPayInvoiceStatus,
    LNURLPayMetadataMismatch,
    LNURLPayRequestExpired,
    LNURLPayRequestNotFound,
    LNURLPayRequestRevoked,
    LNURLPayerDataInvalid,
)
from app.services.lnurl.pay.errors import LNURLPayInvalidAmountError, LNURLPayRequestError
from app.services.lnurl.pay_metadata import LNURLPayMetadataBuilder

NOW = datetime(2026, 7, 17, tzinfo=UTC)


class FakeProvider:
    provider_name = "fake-test-provider"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self.calls: list[dict[str, Any]] = []
        self.fail = fail
        self.malformed = malformed

    async def create_invoice(self, *, amount_msat: int, description_hash: str, expiry_seconds: int, idempotency_key: str, metadata: dict[str, Any]) -> LightningInvoiceResult:
        self.calls.append(
            {
                "amount_msat": amount_msat,
                "description_hash": description_hash,
                "expiry_seconds": expiry_seconds,
                "idempotency_key": idempotency_key,
                "metadata": metadata,
            }
        )
        if self.fail:
            raise RuntimeError("provider secret should not leak")
        if self.malformed:
            return LightningInvoiceResult("", "", "", NOW + timedelta(seconds=expiry_seconds), self.provider_name)
        suffix = idempotency_key[-12:]
        return LightningInvoiceResult(
            provider_invoice_id=f"inv-{suffix}",
            bolt11=f"lnbc{amount_msat}n1{suffix}",
            payment_hash=f"payment-{suffix}",
            expires_at=NOW + timedelta(seconds=expiry_seconds),
            provider_name=self.provider_name,
            verify_url=f"https://verify.example/{suffix}",
        )


class FakeAudit:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record_event(self, **kwargs: Any) -> Any:
        self.events.append(kwargs)

        class Event:
            event_hash = f"audit-{len(self.events)}"

        return Event()


def metadata() -> tuple[str, str]:
    result = LNURLPayMetadataBuilder().build_subscription_metadata(plan_code="pro_pass", duration_label="1 month")
    return result.canonical_json, result.metadata_hash


def request_record(**overrides: Any) -> LNURLPayRequestRecord:
    raw_metadata, metadata_hash = metadata()
    base = LNURLPayRequestRecord(
        request_id="req_1",
        request_reference_hash="sha256:req-ref",
        product_code="bastion_access",
        plan_code="pro_pass",
        principal_hash="hmac-sha256:principal",
        actor_type="lightning_wallet_principal",
        pricing_version="v1",
        fixed_amount_msat=100_000,
        min_amount_msat=100_000,
        max_amount_msat=100_000,
        metadata=raw_metadata,
        metadata_hash=metadata_hash,
        callback_hash="sha256:callback",
        payer_data_policy=None,
        payer_data_policy_hash=None,
        comment_allowed=None,
        success_action_mode="none",
        status=LNURLPayRequestStatus.PENDING_CALLBACK,
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
        idempotency_hash=None,
        request_fingerprint="sha256:fingerprint",
        policy_hash="sha256:policy",
    )
    return replace(base, **overrides)


def service(record: LNURLPayRequestRecord, provider: FakeProvider | None = None, audit: FakeAudit | None = None) -> tuple[LNURLPayCallbackService, InMemoryLNURLPayCallbackRepository, FakeProvider, FakeAudit]:
    repo = InMemoryLNURLPayCallbackRepository({record.request_id: record})
    provider = provider or FakeProvider()
    audit = audit or FakeAudit()
    svc = LNURLPayCallbackService(repository=repo, invoice_provider=provider, audit_chain=audit, clock=lambda: NOW)
    return svc, repo, provider, audit


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_valid_fixed_price_request_issues_invoice_without_settlement_or_entitlement() -> None:
    svc, repo, provider, audit = service(request_record())

    result = run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)))

    assert result.pr.startswith("lnbc")
    assert result.payment_status == LNURLPayInvoiceStatus.INVOICE_ISSUED.value
    assert result.success_action is None
    assert repo.get_request("req_1").status == LNURLPayRequestStatus.INVOICE_ISSUED  # type: ignore[union-attr]
    assert repo.count_entitlements() == 0
    assert repo.count_payment_proofs() == 0
    assert repo.count_sessions() == 0
    assert len(provider.calls) == 1
    assert provider.calls[0]["description_hash"] == result.metadata_hash
    assert audit.events[0]["event_type"] == "lnurl_invoice_issued"
    assert "payer_data" not in str(audit.events[0]).lower()
    assert "preimage" not in str(audit.events[0]).lower()


def test_valid_variable_price_request_succeeds() -> None:
    record = request_record(fixed_amount_msat=None, min_amount_msat=50_000, max_amount_msat=150_000)
    svc, _, provider, _ = service(record)

    result = run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 75_000)))

    assert result.amount_msat == 75_000
    assert len(provider.calls) == 1


@pytest.mark.parametrize("amount", [99_999, 100_001, 0, -1])
def test_invalid_amounts_fail(amount: int) -> None:
    svc, _, _, _ = service(request_record())

    with pytest.raises(LNURLPayInvalidAmountError):
        run(svc.create_invoice(LNURLPayCallbackCommand("req_1", amount)))


def test_unknown_expired_and_revoked_requests_fail() -> None:
    svc, _, _, _ = service(request_record())
    with pytest.raises(LNURLPayRequestNotFound):
        run(svc.create_invoice(LNURLPayCallbackCommand("missing", 100_000)))

    expired, _, _, _ = service(request_record(expires_at=NOW - timedelta(seconds=1)))
    with pytest.raises(LNURLPayRequestExpired):
        run(expired.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)))

    revoked, _, _, _ = service(request_record(status=LNURLPayRequestStatus.REVOKED, revoked_at=NOW))
    with pytest.raises(LNURLPayRequestRevoked):
        run(revoked.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)))


def test_metadata_integrity_is_enforced_and_callback_cannot_replace_metadata() -> None:
    record = request_record(metadata_hash="sha256:tampered")
    svc, _, _, _ = service(record)

    with pytest.raises(LNURLPayMetadataMismatch):
        run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, client_context={"plan_code": "enterprise_pass"})))


def test_comment_rules_and_comment_not_authorization() -> None:
    no_comment, _, _, _ = service(request_record())
    with pytest.raises(LNURLPayCommentNotAllowed):
        run(no_comment.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, comment="please grant access")))

    comment_record = request_record(comment_allowed=12)
    too_long, _, _, _ = service(comment_record)
    with pytest.raises(LNURLPayCommentTooLong):
        run(too_long.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, comment="x" * 13)))

    ok, _, _, _ = service(comment_record)
    result = run(ok.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, comment="order 123")))
    assert result.payment_status == "invoice_issued"


def test_payer_data_is_untrusted_and_does_not_grant_entitlement() -> None:
    svc, _, _, _ = service(request_record())
    with pytest.raises(LNURLPayerDataInvalid):
        run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, payer_data={"email": "a@example.com"})))

    record = request_record(payer_data_policy={"auth": {"mandatory": False}})
    ok, repo, _, _ = service(record)
    result = run(ok.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, payer_data={"auth": {"k1_hash": "sha256:k"}})))
    assert result.payment_status == "invoice_issued"
    assert repo.count_entitlements() == 0

    bad, _, _, _ = service(record)
    with pytest.raises(LNURLPayerDataInvalid):
        run(bad.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, payer_data={"email": "a@example.com"})))


def test_idempotent_retry_returns_same_invoice_and_conflict_fails() -> None:
    svc, _, provider, _ = service(request_record(fixed_amount_msat=None, min_amount_msat=100_000, max_amount_msat=200_000))

    first = run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)))
    second = run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)))

    assert first.pr == second.pr
    assert len(provider.calls) == 1
    with pytest.raises(LNURLInvoiceConflict):
        run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_001)))


def test_concurrent_duplicate_callback_creates_one_provider_invoice() -> None:
    svc, _, provider, _ = service(request_record())

    async def call_twice() -> list[Any]:
        return await asyncio.gather(
            svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)),
            svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)),
        )

    results = run(call_twice())
    assert results[0].pr == results[1].pr
    assert len(provider.calls) == 1


def test_provider_unavailable_and_malformed_response_fail_safely() -> None:
    unavailable = LNURLPayCallbackService(repository=InMemoryLNURLPayCallbackRepository({"req_1": request_record()}), clock=lambda: NOW)
    with pytest.raises(LNURLInvoiceProviderUnavailable):
        run(unavailable.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)))

    malformed, _, _, _ = service(request_record(), provider=FakeProvider(malformed=True))
    with pytest.raises(LNURLInvoiceCreationFailed):
        run(malformed.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)))

    failing, _, _, _ = service(request_record(), provider=FakeProvider(fail=True))
    with pytest.raises(LNURLInvoiceCreationFailed) as exc:
        run(failing.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)))
    assert "provider secret" not in str(exc.value).lower()


def test_invoice_ttl_is_capped_by_request_lifetime() -> None:
    record = request_record(expires_at=NOW + timedelta(seconds=120))
    svc, _, provider, _ = service(record)
    svc.config = LNURLPayCallbackConfig(invoice_ttl_seconds=900)

    run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000)))

    assert provider.calls[0]["expiry_seconds"] == 120


def test_secret_material_is_rejected() -> None:
    svc, _, _, _ = service(request_record())

    with pytest.raises(LNURLPayRequestError):
        run(svc.create_invoice(LNURLPayCallbackCommand("req_1", 100_000, client_context={"private_key": "secret"})))
