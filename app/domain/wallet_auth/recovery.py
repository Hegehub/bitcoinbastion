"""Wallet recovery domain primitives."""

from __future__ import annotations

from enum import StrEnum


class WalletRecoveryProfile(StrEnum):
    LITE_BASIC = "lite_basic"
    PLUS_PRO = "plus_pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    SOVEREIGN = "sovereign"


class RecoveryFactorType(StrEnum):
    WALLET_RESIGNATURE = "wallet_resignature"
    LNURL_AUTH_RESIGNATURE = "lnurl_auth_resignature"
    PAYMENT_PROOF = "payment_proof"
    TRUSTED_DEVICE = "trusted_device"
    RECOVERY_FILE = "recovery_file"
    OWNER_WALLET = "owner_wallet"
    ADMIN_WALLET = "admin_wallet"
    HARDWARE_WALLET = "hardware_wallet"
    RECOVERY_CAPSULE = "recovery_capsule"
    TRANSPARENCY_CHECKPOINT = "transparency_checkpoint"
    COOLDOWN = "cooldown"
    MULTI_WALLET_QUORUM = "multi_wallet_quorum"


LITE_BASIC_RECOVERY_FACTORS = frozenset(
    {
        RecoveryFactorType.WALLET_RESIGNATURE,
        RecoveryFactorType.PAYMENT_PROOF,
        RecoveryFactorType.COOLDOWN,
    }
)
PLUS_PRO_RECOVERY_FACTORS = frozenset(
    {
        RecoveryFactorType.WALLET_RESIGNATURE,
        RecoveryFactorType.LNURL_AUTH_RESIGNATURE,
        RecoveryFactorType.TRUSTED_DEVICE,
        RecoveryFactorType.RECOVERY_FILE,
        RecoveryFactorType.COOLDOWN,
    }
)
BUSINESS_RECOVERY_FACTORS = frozenset(
    {
        RecoveryFactorType.OWNER_WALLET,
        RecoveryFactorType.ADMIN_WALLET,
        RecoveryFactorType.TRUSTED_DEVICE,
        RecoveryFactorType.RECOVERY_CAPSULE,
        RecoveryFactorType.COOLDOWN,
    }
)
ENTERPRISE_RECOVERY_FACTORS = frozenset(
    {
        RecoveryFactorType.OWNER_WALLET,
        RecoveryFactorType.ADMIN_WALLET,
        RecoveryFactorType.HARDWARE_WALLET,
        RecoveryFactorType.RECOVERY_CAPSULE,
        RecoveryFactorType.TRANSPARENCY_CHECKPOINT,
        RecoveryFactorType.MULTI_WALLET_QUORUM,
        RecoveryFactorType.COOLDOWN,
    }
)
SOVEREIGN_RECOVERY_FACTORS = frozenset(
    {
        RecoveryFactorType.OWNER_WALLET,
        RecoveryFactorType.ADMIN_WALLET,
        RecoveryFactorType.HARDWARE_WALLET,
        RecoveryFactorType.RECOVERY_CAPSULE,
        RecoveryFactorType.TRANSPARENCY_CHECKPOINT,
        RecoveryFactorType.MULTI_WALLET_QUORUM,
        RecoveryFactorType.COOLDOWN,
    }
)
