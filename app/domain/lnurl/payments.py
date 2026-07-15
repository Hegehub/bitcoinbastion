"""Pure LNURL-pay domain primitives."""

from __future__ import annotations

from enum import StrEnum


class LNURLPaymentStatus(StrEnum):
    CREATED = "created"
    METADATA_READY = "metadata_ready"
    METADATA_ISSUED = "metadata_ready"
    INVOICE_REQUESTED = "invoice_requested"
    INVOICE_ISSUED = "invoice_issued"
    PENDING = "pending"
    SETTLED = "settled"
    SETTLEMENT_VERIFYING = "settlement_verifying"
    VERIFIED = "verified"
    ENTITLEMENT_ISSUED = "verified"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REVOKED = "revoked"


class LNURLPaymentPurpose(StrEnum):
    SUBSCRIPTION = "subscription"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    SUBSCRIPTION_UPGRADE = "subscription_upgrade"
    BUSINESS_INVOICE = "business_invoice"
    ENTERPRISE_INVOICE = "enterprise_invoice"
    PAYREGISTER_PAYMENT = "payregister_payment"
    PAYREGISTER_INVOICE = "payregister_payment"
    MERCHANT_PAYMENT = "merchant_payment"
    DONATION = "donation"
    CONTRIBUTION = "contribution"
    TEST_PAYMENT = "test_payment"


class LNURLPaymentVerificationMethod(StrEnum):
    LNURL_VERIFY = "lnurl_verify"
    INTERNAL_LIGHTNING_NODE = "internal_lightning_node"
    BTCPAY = "btcpay"
    PROVIDER_WEBHOOK = "provider_webhook"
    PAYMENT_PREIMAGE = "payment_preimage"
    MANUAL_TEST_GRANT = "manual_test_grant"


class LNURLMetadataType(StrEnum):
    TEXT_PLAIN = "text_plain"
    TEXT_LONG_DESC = "text_long_desc"
    TEXT_IDENTIFIER = "text_identifier"
    IMAGE_PNG_BASE64 = "image_png_base64"
    IMAGE_JPEG_BASE64 = "image_jpeg_base64"


LNURL_METADATA_MIME_TYPES = {
    LNURLMetadataType.TEXT_PLAIN: "text/plain",
    LNURLMetadataType.TEXT_LONG_DESC: "text/long-desc",
    LNURLMetadataType.TEXT_IDENTIFIER: "text/identifier",
    LNURLMetadataType.IMAGE_PNG_BASE64: "image/png;base64",
    LNURLMetadataType.IMAGE_JPEG_BASE64: "image/jpeg;base64",
}
LNURL_COMMENT_ALLOWED_DEFAULT = 0
LNURL_COMMENT_ALLOWED_MAX = 280


class LNURLCommentPurpose(StrEnum):
    INVOICE_NOTE = "invoice_note"
    MERCHANT_ORDER_REFERENCE = "merchant_order_reference"
    RECEIPT_COMMENT = "receipt_comment"
    SUPPORT_REFERENCE = "support_reference"


_PAYMENT_TRANSITIONS = {
    LNURLPaymentStatus.CREATED: frozenset({LNURLPaymentStatus.METADATA_READY, LNURLPaymentStatus.EXPIRED, LNURLPaymentStatus.CANCELLED, LNURLPaymentStatus.REVOKED}),
    LNURLPaymentStatus.METADATA_READY: frozenset({LNURLPaymentStatus.INVOICE_REQUESTED, LNURLPaymentStatus.EXPIRED, LNURLPaymentStatus.CANCELLED}),
    LNURLPaymentStatus.INVOICE_REQUESTED: frozenset({LNURLPaymentStatus.INVOICE_ISSUED, LNURLPaymentStatus.FAILED, LNURLPaymentStatus.EXPIRED}),
    LNURLPaymentStatus.INVOICE_ISSUED: frozenset({LNURLPaymentStatus.PENDING, LNURLPaymentStatus.SETTLED, LNURLPaymentStatus.EXPIRED, LNURLPaymentStatus.CANCELLED}),
    LNURLPaymentStatus.PENDING: frozenset({LNURLPaymentStatus.SETTLED, LNURLPaymentStatus.EXPIRED, LNURLPaymentStatus.FAILED}),
    LNURLPaymentStatus.SETTLED: frozenset({LNURLPaymentStatus.SETTLEMENT_VERIFYING, LNURLPaymentStatus.VERIFIED}),
    LNURLPaymentStatus.SETTLEMENT_VERIFYING: frozenset({LNURLPaymentStatus.VERIFIED, LNURLPaymentStatus.FAILED}),
    LNURLPaymentStatus.VERIFIED: frozenset(),
    LNURLPaymentStatus.EXPIRED: frozenset(),
    LNURLPaymentStatus.CANCELLED: frozenset(),
    LNURLPaymentStatus.FAILED: frozenset(),
    LNURLPaymentStatus.REVOKED: frozenset(),
}


def can_transition_payment(current: LNURLPaymentStatus | str, target: LNURLPaymentStatus | str) -> bool:
    return LNURLPaymentStatus(target) in _PAYMENT_TRANSITIONS[LNURLPaymentStatus(current)]


def is_terminal_payment_status(status: LNURLPaymentStatus | str) -> bool:
    return not _PAYMENT_TRANSITIONS[LNURLPaymentStatus(status)]


def requires_settlement_verification(status: LNURLPaymentStatus | str) -> bool:
    return LNURLPaymentStatus(status) in {LNURLPaymentStatus.SETTLED, LNURLPaymentStatus.SETTLEMENT_VERIFYING}
