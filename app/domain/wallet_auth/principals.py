"""Wallet principal domain enums."""

from __future__ import annotations

from enum import StrEnum


class WalletPrincipalStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    RECOVERY_LOCKED = "recovery_locked"
    PENDING_VERIFICATION = "pending_verification"


class WalletPrincipalActorType(StrEnum):
    BITCOIN_WALLET_PRINCIPAL = "bitcoin_wallet_principal"
    LIGHTNING_WALLET_PRINCIPAL = "lightning_wallet_principal"
    WALLET_DEVICE = "wallet_device"
    ACCESS_CERTIFICATE = "access_certificate"
    CHILD_API_KEY = "child_api_key"
    DELEGATED_PASS = "delegated_pass"
    BUSINESS_ROLE = "business_role"
    PAYREGISTER_DEVICE = "payregister_device"
    BOT = "bot"
