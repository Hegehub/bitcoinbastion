"""LNURL-pay domain enums."""

from __future__ import annotations

from enum import StrEnum


class LNURLPaymentStatus(StrEnum):
    CREATED = "created"
    METADATA_ISSUED = "metadata_issued"
    INVOICE_REQUESTED = "invoice_requested"
    INVOICE_ISSUED = "invoice_issued"
    PENDING = "pending"
    SETTLED = "settled"
    EXPIRED = "expired"
    FAILED = "failed"
    VERIFIED = "verified"
    ENTITLEMENT_ISSUED = "entitlement_issued"


class LNURLPaymentPurpose(StrEnum):
    SUBSCRIPTION = "subscription"
    PAYREGISTER_INVOICE = "payregister_invoice"
    BUSINESS_INVOICE = "business_invoice"
    ENTERPRISE_INVOICE = "enterprise_invoice"
    DONATION = "donation"
    TEST_PAYMENT = "test_payment"
