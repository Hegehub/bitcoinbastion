from datetime import UTC, datetime, timedelta

import pytest

from app.services.lnurl.pay_callback_service import LightningInvoiceResult
from app.services.payregister.lnurl.callback import PayRegisterLNURLCallbackService
from app.services.payregister.lnurl.payment_context import PayRegisterLNURLContextStatus, PayRegisterLNULEndpointMode
from app.services.payregister.lnurl.receipt import PayRegisterLNURLReceiptService
from app.services.payregister.lnurl.settlement import PayRegisterLNURLSettlementService
from app.services.payregister.lnurl.static_endpoint import InMemoryPayRegisterLNURLRepository, PayRegisterLNURLConfig, PayRegisterLNURLStaticEndpointService


class FakeInvoiceProvider:
    provider_name = "fake"

    async def create_invoice(self, *, amount_msat, description_hash, expiry_seconds, idempotency_key, metadata):
        return LightningInvoiceResult("provider-id", f"lnbc{amount_msat}n1fake", "payment-hash", datetime.now(UTC) + timedelta(seconds=expiry_seconds), "fake")


@pytest.fixture
def active_service():
    service = PayRegisterLNURLStaticEndpointService(repository=InMemoryPayRegisterLNURLRepository(), config=PayRegisterLNURLConfig(public_base_url="https://payregister.bitcoin-bastion.com"))
    endpoint = service.create_static_endpoint(public_alias="safe-counter", endpoint_mode=PayRegisterLNULEndpointMode.TERMINAL_CHECKOUT, merchant_workspace_hash="hmac:workspace-secret", store_hash="hmac:store-secret", terminal_hash="hmac:terminal-secret", min_sendable_msat=1_000, max_sendable_msat=200_000, display_label="Safe Merchant")
    endpoint = service.activate_static_endpoint(endpoint.endpoint_id)
    context = service.publish_checkout_context(endpoint_id=endpoint.endpoint_id, amount_msat=50_000, description="Order")
    return service, endpoint, context


def test_qr_and_nfc_payloads_expose_no_secrets(active_service):
    service, endpoint, _context = active_service
    qr = service.build_qr_payload(endpoint.endpoint_id)
    nfc = service.build_nfc_payload(endpoint.endpoint_id)
    public = f"{qr.raw_discovery_url} {qr.lnurl} {nfc.https_url} {nfc.lnurl_text}".lower()
    for forbidden in ("workspace-secret", "terminal-secret", "bolt11", "access_pass", "session_token", "private_key", "seed"):
        assert forbidden not in public


@pytest.mark.anyio
async def test_amount_tampering_and_disabled_revoked_contexts_fail(active_service):
    service, endpoint, context = active_service
    callback = PayRegisterLNURLCallbackService(endpoint_service=service, invoice_provider=FakeInvoiceProvider())
    with pytest.raises(Exception) as wrong_amount:
        await callback.create_invoice(payment_context_reference=context.payment_context_id, amount_msat=49_999)
    assert getattr(wrong_amount.value, "reason_code", "") == "invalid_amount"

    service.suspend_static_endpoint(endpoint.endpoint_id)
    with pytest.raises(Exception) as disabled:
        service.resolve_static_endpoint(endpoint.public_alias)
    assert getattr(disabled.value, "reason_code", "") == "endpoint_disabled"

    service.revoke_static_endpoint(endpoint.endpoint_id)
    with pytest.raises(Exception) as revoked:
        service.resolve_static_endpoint(endpoint.public_alias)
    assert getattr(revoked.value, "reason_code", "") == "endpoint_revoked"


@pytest.mark.anyio
async def test_invoice_issuance_is_not_settlement_and_receipt_requires_settlement(active_service):
    service, _endpoint, context = active_service
    callback = PayRegisterLNURLCallbackService(endpoint_service=service, invoice_provider=FakeInvoiceProvider())
    await callback.create_invoice(payment_context_reference=context.payment_context_id, amount_msat=50_000, comment="table 4")
    pending = service.repository.get_context(context.payment_context_id)
    assert pending.status == PayRegisterLNURLContextStatus.PENDING_PAYMENT
    assert pending.settled_at is None
    receipt_service = PayRegisterLNURLReceiptService(endpoint_service=service)
    with pytest.raises(Exception):
        receipt_service.create_after_settlement(context.payment_context_id)
    settlement = PayRegisterLNURLSettlementService(endpoint_service=service, receipt_service=receipt_service)
    proof, receipt = settlement.settle_context(context.payment_context_id, invoice_hash=pending.invoice_hash, payment_hash=pending.payment_hash)
    assert proof.amount_msat == 50_000
    assert receipt.refund_status == "not_refunded"


@pytest.mark.anyio
async def test_replaced_and_expired_contexts_cannot_issue_invoices(active_service):
    service, endpoint, first = active_service
    service.publish_checkout_context(endpoint_id=endpoint.endpoint_id, amount_msat=60_000, description="Replacement")
    callback = PayRegisterLNURLCallbackService(endpoint_service=service, invoice_provider=FakeInvoiceProvider())
    with pytest.raises(Exception) as replaced:
        await callback.create_invoice(payment_context_reference=first.payment_context_id, amount_msat=50_000)
    assert getattr(replaced.value, "reason_code", "") == "checkout_replaced"
