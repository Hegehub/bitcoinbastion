from datetime import UTC, datetime, timedelta

import pytest

from app.domain.payregister_lnurl.roles import PayRegisterActorType, PayRegisterCashierRole
from app.domain.payregister_lnurl.statuses import PayRegisterPaymentContextStatus, PayRegisterReceiptStatus, PayRegisterTerminalStatus
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.lnurl.pay_callback_service import LightningInvoiceResult
from app.services.payregister.context_integrity import compute_context_hash, verify_settlement_context_binding
from app.services.payregister.lnurl.callback import PayRegisterLNURLCallbackService
from app.services.payregister.lnurl.payment_context import PayRegisterLNURLContextStatus, PayRegisterLNULEndpointMode
from app.services.payregister.lnurl.receipt import PayRegisterLNURLReceiptService as LNURLReceiptService
from app.services.payregister.lnurl.settlement import PayRegisterLNURLSettlementService
from app.services.payregister.lnurl.static_endpoint import InMemoryPayRegisterLNURLRepository, PayRegisterLNURLStaticEndpointService
from app.services.payregister.lnurl_context import PayRegisterContextBuildRequest, PayRegisterContextBuilder
from app.services.payregister.receipt_service import PayRegisterReceiptInput, PayRegisterReceiptService
from app.services.payregister.role_binding_service import PayRegisterRoleBinding, PayRegisterRoleBindingService
from app.services.payregister.shift_service import PayRegisterShiftService


class FakeInvoiceProvider:
    provider_name = "fake"
    async def create_invoice(self, *, amount_msat, description_hash, expiry_seconds, idempotency_key, metadata):
        return LightningInvoiceResult("provider-invoice", f"lnbc{amount_msat}n1fake", "payment-hash", datetime.now(UTC) + timedelta(seconds=expiry_seconds), "fake")


def binding(**overrides):
    values = dict(role_binding_hash="hmac:role", workspace_hash="hmac:workspace", store_hash="hmac:store", terminal_hash="hmac:terminal", shift_hash="hmac:preopen", actor_type=PayRegisterActorType.CASHIER, role=PayRegisterCashierRole.CASHIER)
    values.update(overrides)
    return PayRegisterRoleBinding(**values)


@pytest.mark.anyio
async def test_payregister_lnurl_cashier_shift_payment_receipt_flow():
    role_service = PayRegisterRoleBindingService()
    shift_service = PayRegisterShiftService(role_service=role_service)
    shift = shift_service.open_shift(binding=binding(), opening_device_fingerprint="sha256:device")
    role_context = role_service.validate_role_binding(binding(shift_hash=shift.shift_hash))
    context = PayRegisterContextBuilder().build_context(PayRegisterContextBuildRequest(role_context=role_context, terminal_device_fingerprint="sha256:device", amount_msat=2500000, order_reference="9231", merchant_invoice_reference="INV-9231", store_display_name="Store 12", terminal_display_name="Terminal 3", public_lightning_identifier="store-12@payregister.bitcoin-bastion.com"))
    context_hash = compute_context_hash(context)

    endpoint_service = PayRegisterLNURLStaticEndpointService(repository=InMemoryPayRegisterLNURLRepository())
    endpoint = endpoint_service.create_static_endpoint(public_alias="store-12", endpoint_mode=PayRegisterLNULEndpointMode.TERMINAL_CHECKOUT, merchant_workspace_hash=context.workspace_hash, store_hash=context.store_hash, terminal_hash=context.terminal_hash, min_sendable_msat=1_000, max_sendable_msat=5_000_000, display_label="Store 12")
    endpoint_service.activate_static_endpoint(endpoint.endpoint_id)
    lnurl_context = endpoint_service.publish_checkout_context(endpoint_id=endpoint.endpoint_id, amount_msat=context.amount_msat, description="Order 9231", order_reference="9231", cashier_context=context)
    pay_request = endpoint_service.resolve_lnurl_pay_request("store-12")
    assert pay_request.min_sendable_msat == pay_request.max_sendable_msat == context.amount_msat
    assert lnurl_context.shift_hash == shift.shift_hash

    callback = PayRegisterLNURLCallbackService(endpoint_service=endpoint_service, invoice_provider=FakeInvoiceProvider())
    invoice = await callback.create_invoice(payment_context_reference=lnurl_context.payment_context_id, amount_msat=context.amount_msat)
    pending = endpoint_service.repository.get_context(lnurl_context.payment_context_id)
    assert invoice.pr.startswith("lnbc2500000")
    assert pending.status == PayRegisterLNURLContextStatus.PENDING_PAYMENT

    verify_settlement_context_binding(context=context, context_hash=context_hash, metadata_hash=context.metadata_hash, amount_msat=context.amount_msat, payment_hash=pending.payment_hash, expected_payment_hash=pending.payment_hash)
    lnurl_receipts = LNURLReceiptService(endpoint_service=endpoint_service)
    settlement = PayRegisterLNURLSettlementService(endpoint_service=endpoint_service, receipt_service=lnurl_receipts)
    proof, _receipt = settlement.settle_context(lnurl_context.payment_context_id, invoice_hash=pending.invoice_hash, payment_hash=pending.payment_hash)

    receipt_packet = PayRegisterReceiptService().issue_receipt(PayRegisterReceiptInput(context=context, payment_proof_hash=proof.proof_fingerprint, lnurl_payment_request_hash=sha256_prefixed(lnurl_context.payment_context_id), settled_at=datetime.now(UTC), audit_event_hash=sha256_prefixed("audit")))
    assert receipt_packet.status == PayRegisterReceiptStatus.ISSUED
    assert receipt_packet.shift_hash == shift.shift_hash
    closed = shift_service.close_shift(shift.shift_id)
    assert closed.closed_at is not None
    assert PayRegisterPaymentContextStatus.SETTLED.value == "settled"


def test_revoked_terminal_negative_flow_denied_and_audited():
    shift_service = PayRegisterShiftService()
    with pytest.raises(Exception):
        shift_service.open_shift(binding=binding(terminal_status=PayRegisterTerminalStatus.REVOKED), opening_device_fingerprint="sha256:device")
    assert any(event["event_type"] == "payregister_shift_open_denied" for event in shift_service.repository.audit_events)
