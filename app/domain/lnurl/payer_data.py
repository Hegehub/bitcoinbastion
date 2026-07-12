"""LNURL payerData and comment policy primitives."""

from __future__ import annotations

from enum import StrEnum


class LNURLPayerDataField(StrEnum):
    NAME = "name"
    PUBKEY = "pubkey"
    IDENTIFIER = "identifier"
    EMAIL = "email"
    AUTH = "auth"


DEFAULT_ALLOWED_PAYERDATA_FIELDS = [LNURLPayerDataField.AUTH.value]
PRIVACY_SENSITIVE_PAYERDATA_FIELDS = [
    LNURLPayerDataField.EMAIL.value,
    LNURLPayerDataField.NAME.value,
    LNURLPayerDataField.IDENTIFIER.value,
]


class LNURLCommentPolicy(StrEnum):
    DISABLED = "disabled"
    ALLOWED_UNTRUSTED = "allowed_untrusted"
    ALLOWED_RECEIPT_ONLY = "allowed_receipt_only"
