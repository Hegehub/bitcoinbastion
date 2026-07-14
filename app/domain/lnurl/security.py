"""LNURL security domain enums."""

from __future__ import annotations

from enum import StrEnum


class LNURLK1Status(StrEnum):
    UNUSED = "unused"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNEXPECTED = "unexpected"
    REPLAY_REJECTED = "replay_rejected"


class LNURLSecurityLevel(StrEnum):
    COMPATIBILITY = "compatibility"
    STANDARD = "standard"
    HIGH_ASSURANCE = "high_assurance"
    BUSINESS = "business"
    SOVEREIGN = "sovereign"
