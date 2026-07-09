"""Wallet session domain constants and enums."""

from __future__ import annotations

from enum import StrEnum


class WalletSessionStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FROZEN = "frozen"
    LOCKDOWN = "lockdown"
    RECOVERY_ONLY = "recovery_only"


DEFAULT_WALLET_CHALLENGE_TTL_SECONDS = 300
DEFAULT_WALLET_SESSION_TTL_SECONDS = 900
DEFAULT_STEP_UP_TTL_SECONDS = 300
