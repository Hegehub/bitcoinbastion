"""PayRegister LNURL settlement orchestration."""
from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from app.services.payregister.lnurl.errors import PayRegisterLNURLSettlementError
from app.services.payregister.lnurl.payment_context import PayRegisterLNURLContextStatus
from app.services.payregister.lnurl.receipt import PayRegisterLNURLPaymentProof, PayRegisterLNURLReceipt, PayRegisterLNURLReceiptService
from app.services.payregister.lnurl.static_endpoint import PayRegisterLNURLStaticEndpointService


class PayRegisterLNURLSettlementService:
    def __init__(self, *, endpoint_service: PayRegisterLNURLStaticEndpointService, receipt_service: PayRegisterLNURLReceiptService) -> None:
        self.endpoint_service = endpoint_service
        self.receipt_service = receipt_service

    def settle_context(self, context_id: str, *, invoice_hash: str, payment_hash: str, settlement_method: str = "trusted_test_settlement", settled_at: datetime | None = None) -> tuple[PayRegisterLNURLPaymentProof, PayRegisterLNURLReceipt]:
        context = self.endpoint_service.repository.get_context(context_id)
        if context is None:
            raise PayRegisterLNURLSettlementError("Payment context unavailable")
        if context.status == PayRegisterLNURLContextStatus.SETTLED:
            return self.receipt_service.create_after_settlement(context_id, settlement_method=settlement_method)
        if context.status != PayRegisterLNURLContextStatus.PENDING_PAYMENT:
            raise PayRegisterLNURLSettlementError("Invoice has not been issued")
        if context.invoice_hash != invoice_hash or context.payment_hash != payment_hash:
            raise PayRegisterLNURLSettlementError("Settlement proof does not match issued invoice")
        now = settled_at or datetime.now(UTC)
        updated = replace(context, status=PayRegisterLNURLContextStatus.SETTLED, settled_at=now)
        self.endpoint_service.repository.save_context(updated)
        self.endpoint_service.repository.append_audit("payregister_lnurl_payment_settled", {"context_hash": invoice_hash, "payment_hash": payment_hash})
        return self.receipt_service.create_after_settlement(context_id, settlement_method=settlement_method)
