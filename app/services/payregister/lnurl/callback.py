"""PayRegister LNURL-pay callback invoice bridge."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.pay.subscription_request_service import LNURLPayRequestRecord, LNURLPayRequestStatus
from app.services.lnurl.pay_callback_service import (
    InMemoryLNURLPayCallbackRepository,
    LNURLPayCallbackCommand,
    LNURLPayCallbackConfig,
    LNURLPayCallbackService,
    LNURLPayInvoiceResult,
    LightningInvoiceProvider,
)
from app.services.payregister.lnurl.errors import PayRegisterLNURLContextExpired, PayRegisterLNURLContextReplaced, PayRegisterLNURLInvalidAmount
from app.services.payregister.lnurl.payment_context import PayRegisterLNURLContextStatus, PayRegisterLNURLPaymentContext
from app.services.payregister.lnurl.static_endpoint import PayRegisterLNURLStaticEndpointService


class PayRegisterLNURLCallbackService:
    def __init__(self, *, endpoint_service: PayRegisterLNURLStaticEndpointService, invoice_provider: LightningInvoiceProvider, callback_config: LNURLPayCallbackConfig | None = None) -> None:
        self.endpoint_service = endpoint_service
        self.invoice_provider = invoice_provider
        self.callback_config = callback_config or LNURLPayCallbackConfig()
        self._requests: dict[str, LNURLPayRequestRecord] = {}
        self._lnurl_repo = InMemoryLNURLPayCallbackRepository(self._requests)
        self._lnurl_callback = LNURLPayCallbackService(repository=self._lnurl_repo, invoice_provider=invoice_provider, config=self.callback_config)

    async def create_invoice(self, *, payment_context_reference: str, amount_msat: int, comment: str | None = None, payer_data: dict[str, Any] | None = None) -> LNURLPayInvoiceResult:
        context = self.endpoint_service.repository.get_context(payment_context_reference)
        if context is None:
            raise PayRegisterLNURLContextExpired("Checkout unavailable")
        now = datetime.now(UTC)
        if context.status == PayRegisterLNURLContextStatus.REPLACED:
            raise PayRegisterLNURLContextReplaced("Checkout was replaced")
        if context.expires_at <= now or context.status == PayRegisterLNURLContextStatus.EXPIRED:
            raise PayRegisterLNURLContextExpired("Checkout expired")
        if amount_msat < context.min_sendable_msat or amount_msat > context.max_sendable_msat:
            raise PayRegisterLNURLInvalidAmount("Amount outside PayRegister context bounds")
        if context.amount_msat is not None and amount_msat != context.amount_msat:
            raise PayRegisterLNURLInvalidAmount("PayRegister exact checkout amount mismatch")
        self._requests[context.payment_context_id] = self._request_from_context(context)
        result = await self._lnurl_callback.create_invoice(
            LNURLPayCallbackCommand(request_id=context.payment_context_id, amount_msat=amount_msat, comment=comment, payer_data=payer_data)
        )
        invoice = self._lnurl_repo.get_invoice_by_request_id(context.payment_context_id)
        if invoice is not None:
            self.endpoint_service.mark_invoice_issued(
                context.payment_context_id,
                invoice_hash=invoice.invoice_hash,
                payment_hash=invoice.payment_hash,
                provider_invoice_id_hash=invoice.provider_invoice_id_hash,
            )
        return result

    def _request_from_context(self, context: PayRegisterLNURLPaymentContext) -> LNURLPayRequestRecord:
        return LNURLPayRequestRecord(
            request_id=context.payment_context_id,
            request_reference_hash=context.public_endpoint_hash,
            product_code="payregister_static_endpoint",
            plan_code="merchant_payment",
            principal_hash=None,
            actor_type=None,
            pricing_version="payregister-lnurl-static-v1",
            fixed_amount_msat=context.amount_msat,
            min_amount_msat=context.min_sendable_msat,
            max_amount_msat=context.max_sendable_msat,
            metadata=context.metadata,
            metadata_hash=context.metadata_hash,
            callback_hash=context.callback_token_hash,
            payer_data_policy=None,
            payer_data_policy_hash=None,
            comment_allowed=280,
            success_action_mode="url",
            status=LNURLPayRequestStatus.PENDING_CALLBACK,
            created_at=context.created_at,
            expires_at=context.expires_at,
            idempotency_hash=None,
            request_fingerprint=sha256_prefixed(context.payment_context_id),
            policy_hash=hmac_sha256_prefixed("payregister-lnurl-policy", context.metadata_hash),
        )
