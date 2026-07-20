"""Stable PayRegister LNURL state vocabulary."""
from __future__ import annotations

from enum import StrEnum


class PayRegisterShiftStatus(StrEnum):
    SCHEDULED = "scheduled"
    OPENING = "opening"
    ACTIVE = "active"
    CLOSING = "closing"
    CLOSED = "closed"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


class PayRegisterTerminalStatus(StrEnum):
    PENDING_ENROLLMENT = "pending_enrollment"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    OFFLINE_LIMITED = "offline_limited"
    MAINTENANCE = "maintenance"


class PayRegisterPaymentContextStatus(StrEnum):
    CREATED = "created"
    AWAITING_INVOICE = "awaiting_invoice"
    INVOICE_ISSUED = "invoice_issued"
    PAYMENT_PENDING = "payment_pending"
    SETTLED = "settled"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"
    FAILED = "failed"


class PayRegisterReceiptStatus(StrEnum):
    PENDING = "pending"
    ISSUED = "issued"
    VERIFIED = "verified"
    VOIDED = "voided"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
