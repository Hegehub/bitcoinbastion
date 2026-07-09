"""LNURL verification domain enums."""

from __future__ import annotations

from enum import StrEnum


class LNURLVerifyStatus(StrEnum):
    NOT_AVAILABLE = "not_available"
    PENDING = "pending"
    SETTLED_TRUE = "settled_true"
    SETTLED_FALSE = "settled_false"
    PREIMAGE_VERIFIED = "preimage_verified"
    FAILED = "failed"
    EXPIRED = "expired"
