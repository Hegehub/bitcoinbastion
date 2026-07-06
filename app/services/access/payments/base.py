"""Payment provider protocol and safe value objects for Access payments."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


PAYMENT_STATUS_PENDING = "pending"
PAYMENT_STATUS_INVOICE_CREATED = "invoice_created"
PAYMENT_STATUS_PAID = "paid"
PAYMENT_STATUS_EXPIRED = "expired"
PAYMENT_STATUS_INVALID = "invalid"
PAYMENT_STATUS_CANCELLED = "cancelled"
PAYMENT_STATUS_FAILED = "failed"
PAYMENT_STATUS_PAID_LATE_REVIEW_REQUIRED = "paid_late_review_required"
PAYMENT_STATUS_MANUAL_REVIEW_REQUIRED = "manual_review_required"

FINAL_PAYMENT_STATUSES = {
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_PAID_LATE_REVIEW_REQUIRED,
    PAYMENT_STATUS_MANUAL_REVIEW_REQUIRED,
    PAYMENT_STATUS_CANCELLED,
    PAYMENT_STATUS_INVALID,
}


class PaymentProviderNotConfiguredError(RuntimeError):
    """Raised when no trusted payment provider is configured for a method."""


class PaymentProviderDisabledError(RuntimeError):
    """Raised when a provider exists but is disabled by configuration."""


class PaymentIntentNotFoundError(RuntimeError):
    """Raised when an Access payment intent cannot be found."""


class PaymentIntentAlreadyFinalizedError(RuntimeError):
    """Raised when a finalized intent receives an unsafe transition."""


class PaymentWebhookVerificationError(RuntimeError):
    """Raised when a payment webhook cannot be trusted or parsed."""


class ManualGrantsDisabledError(PaymentProviderDisabledError):
    """Raised when the manual grant provider is not explicitly enabled."""


class InvalidPaymentStateTransitionError(RuntimeError):
    """Raised when a payment state transition would be unsafe."""


@dataclass(frozen=True, slots=True)
class PaymentProviderInvoice:
    provider: str
    provider_invoice_id: str
    checkout_url: str | None
    amount_sats: int
    currency: str
    status: str
    expires_at: datetime | None
    raw_metadata_redacted: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PaymentProviderWebhookEvent:
    provider: str
    provider_invoice_id: str
    event_type: str
    status: str
    settled: bool
    expired: bool
    invalid: bool
    occurred_at: datetime
    raw_event_hash: str
    metadata_redacted: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PaymentProviderInvoiceStatus:
    provider: str
    provider_invoice_id: str
    status: str
    settled: bool
    expired: bool
    invalid: bool
    checked_at: datetime


class PaymentProvider(Protocol):
    provider_name: str

    def create_invoice(
        self,
        plan_code: str,
        amount_sats: int,
        metadata: dict[str, Any],
    ) -> PaymentProviderInvoice: ...

    def get_invoice_status(self, provider_invoice_id: str) -> PaymentProviderInvoiceStatus: ...

    def verify_webhook(self, payload: bytes, headers: Mapping[str, str]) -> bool: ...

    def parse_webhook_event(
        self,
        payload: bytes,
        headers: Mapping[str, str],
    ) -> PaymentProviderWebhookEvent: ...
