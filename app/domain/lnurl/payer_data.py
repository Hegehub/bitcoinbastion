"""LNURL payerData and comment domain primitives."""

from __future__ import annotations

from enum import StrEnum


class LNURLPayerDataField(StrEnum):
    NAME = "name"
    PUBKEY = "pubkey"
    IDENTIFIER = "identifier"
    EMAIL = "email"
    AUTH = "auth"


class LNURLPayerDataRequirement(StrEnum):
    PROHIBITED = "prohibited"
    OPTIONAL = "optional"
    REQUESTED = "requested"
    MANDATORY_BY_EXPLICIT_BUSINESS_POLICY = "mandatory_by_explicit_business_policy"


DEFAULT_ALLOWED_PAYER_DATA_FIELDS = frozenset({LNURLPayerDataField.AUTH})
DEFAULT_OPTIONAL_PAYER_DATA_FIELDS = frozenset({LNURLPayerDataField.PUBKEY, LNURLPayerDataField.IDENTIFIER})
DEFAULT_PROHIBITED_PAYER_DATA_FIELDS = frozenset({LNURLPayerDataField.NAME, LNURLPayerDataField.EMAIL})
DEFAULT_ALLOWED_PAYERDATA_FIELDS = tuple(field.value for field in DEFAULT_ALLOWED_PAYER_DATA_FIELDS)
PRIVACY_SENSITIVE_PAYERDATA_FIELDS = tuple(field.value for field in DEFAULT_PROHIBITED_PAYER_DATA_FIELDS | {LNURLPayerDataField.IDENTIFIER})


class LNURLPayerDataStatus(StrEnum):
    ABSENT = "absent"
    RECEIVED = "received"
    VALIDATED = "validated"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REDACTED = "redacted"


class LNURLCommentPolicy(StrEnum):
    DISABLED = "disabled"
    ALLOWED_UNTRUSTED = "allowed_untrusted"
    ALLOWED_RECEIPT_ONLY = "allowed_receipt_only"
