from datetime import UTC, datetime, timedelta

import pytest

from app.services.lnurl.pay_callback_service import LightningInvoiceResult
from app.services.payregister.lnurl.callback import PayRegisterLNURLCallbackService
from app.services.payregister.lnurl.payment_context import PayRegisterLNURLContextStatus, PayRegisterLNULEndpointMode
from app.services.payregister.lnurl.receipt import PayRegisterLNURLReceiptService
from app.services.payregister.lnurl.settlement import PayRegisterLNURLSettlementService
from app.services.payregister.lnurl.static_endpoint import InMemoryPayRegisterLNURLRepository, PayRegisterLNURLStaticEndpointService


class FakeInvoiceProvider:
    provider_name = "fake"

    def __init__(self):
        self.calls = 0

    async def create_invoice(self, *, amount_msat, description_hash, expiry_seconds, idempotency_key, metadata):
        self.calls += 1
        return LightningInvoiceResult(
            provider_invoice_id=f"inv-{idempotency_key[:8]}",
            bolt11=f"lnbc{amount_msat}n1fake",
            payment_hash=f"payment-{idempotency_key[:16]}",
            expires_at=datetime.now(UTC) + timedelta(seconds=expiry_seconds),
            provider_name=self.provider_name,
            verify_url="https://payregister.bitcoin-bastion.com/api/v1/payregister/lnurl/pay/verify/context",
        )


@pytest.mark.anyio
async def test_static_qr_full_checkout_invoice_settlement_receipt_flow():
    endpoint_service = PayRegisterLNURLStaticEndpointService(repository=InMemoryPayRegisterLNURLRepository())
    endpoint = endpoint_service.create_static_endpoint(public_alias="counter-east", endpoint_mode=PayRegisterLNULEndpointMode.TERMINAL_CHECKOUT, merchant_workspace_hash="hmac:workspace", store_hash="hmac:store", terminal_hash="hmac:terminal", min_sendable_msat=1_000, max_sendable_msat=500_000, display_label="Coffee Shop")
    endpoint = endpoint_service.activate_static_endpoint(endpoint.endpoint_id)
    qr = endpoint_service.build_qr_payload(endpoint.endpoint_id)
    nfc = endpoint_service.build_nfc_payload(endpoint.endpoint_id)
    assert qr.raw_discovery_url == nfc.https_url

    context = endpoint_service.publish_checkout_context(endpoint_id=endpoint.endpoint_id, amount_msat=120_000, description="Two coffees", order_reference="ORDER-9")
    pay_request = endpoint_service.resolve_lnurl_pay_request("counter-east")
    assert pay_request.tag == "payRequest"
    assert pay_request.min_sendable_msat == pay_request.max_sendable_msat == 120_000
    assert pay_request.metadata_hash == context.metadata_hash

    provider = FakeInvoiceProvider()
    callback = PayRegisterLNURLCallbackService(endpoint_service=endpoint_service, invoice_provider=provider)
    invoice = await callback.create_invoice(payment_context_reference=context.payment_context_id, amount_msat=120_000)
    assert invoice.pr.startswith("lnbc120000")
    assert provider.calls == 1
    updated = endpoint_service.repository.get_context(context.payment_context_id)
    assert updated.status == PayRegisterLNURLContextStatus.PENDING_PAYMENT
    assert updated.settled_at is None

    invoice_retry = await callback.create_invoice(payment_context_reference=context.payment_context_id, amount_msat=120_000)
    assert invoice_retry.pr == invoice.pr
    assert provider.calls == 1

    receipt_service = PayRegisterLNURLReceiptService(endpoint_service=endpoint_service)
    settlement = PayRegisterLNURLSettlementService(endpoint_service=endpoint_service, receipt_service=receipt_service)
    proof, receipt = settlement.settle_context(context.payment_context_id, invoice_hash=updated.invoice_hash, payment_hash=updated.payment_hash)
    assert proof.proof_type == "bastion_payregister_lnurl_payment_proof"
    assert receipt.receipt_id.startswith("BPR-")
    settled = endpoint_service.repository.get_context(context.payment_context_id)
    assert settled.status == PayRegisterLNURLContextStatus.SETTLED

    proof_again, receipt_again = settlement.settle_context(context.payment_context_id, invoice_hash=updated.invoice_hash, payment_hash=updated.payment_hash)
    assert proof_again.proof_fingerprint == proof.proof_fingerprint
    assert receipt_again.receipt_id == receipt.receipt_id

    replacement = endpoint_service.publish_checkout_context(endpoint_id=endpoint.endpoint_id, amount_msat=130_000, description="Replacement")
    assert replacement.status == PayRegisterLNURLContextStatus.ACTIVE
    assert any(event["event_type"] == "payregister_lnurl_receipt_created" for event in endpoint_service.repository.audit_events)
