"""PayRegister LNURL payment context model."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class PayRegisterLNULEndpointMode(StrEnum):
    TERMINAL_CHECKOUT = "terminal_checkout"
    STORE_OPEN_AMOUNT = "store_open_amount"
    FIXED_PRODUCT = "fixed_product"
    CHECKOUT_ROTATING = "checkout_rotating"


class PayRegisterLNURLAmountMode(StrEnum):
    EXACT = "exact"
    OPEN = "open"
    FIXED_PRODUCT = "fixed_product"


class PayRegisterLNURLContextStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    RESOLVED = "resolved"
    INVOICE_ISSUED = "invoice_issued"
    PENDING_PAYMENT = "pending_payment"
    SETTLED = "settled"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    REPLACED = "replaced"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass(frozen=True, slots=True)
class PayRegisterLNURLPaymentContext:
    payment_context_id: str
    public_endpoint_hash: str
    merchant_workspace_hash: str
    store_hash: str
    mode: PayRegisterLNULEndpointMode
    context_version: int
    amount_mode: PayRegisterLNURLAmountMode
    min_sendable_msat: int
    max_sendable_msat: int
    currency: str
    metadata: str
    metadata_hash: str
    callback_token_hash: str
    status: PayRegisterLNURLContextStatus
    created_at: datetime
    expires_at: datetime
    terminal_hash: str | None = None
    cashier_context_hash: str | None = None
    shift_hash: str | None = None
    checkout_reference_hash: str | None = None
    order_reference_hash: str | None = None
    amount_msat: int | None = None
    quote_hash: str | None = None
    invoice_issued_at: datetime | None = None
    settled_at: datetime | None = None
    invoice_hash: str | None = None
    payment_hash: str | None = None
    provider_invoice_id_hash: str | None = None
    receipt_id: str | None = None
    receipt_reference_hash: str | None = None
    payment_proof_hash: str | None = None
    audit_event_hash: str | None = None

    def is_payable(self, now: datetime | None = None) -> bool:
        checked_at = now or datetime.now(UTC)
        return self.status in {PayRegisterLNURLContextStatus.ACTIVE, PayRegisterLNURLContextStatus.RESOLVED} and self.expires_at > checked_at

