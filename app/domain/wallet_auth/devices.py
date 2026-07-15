"""Wallet device domain enums."""

from __future__ import annotations

from enum import StrEnum


class WalletDeviceClass(StrEnum):
    DESKTOP_VAULT = "desktop_vault"
    MOBILE_VAULT = "mobile_vault"
    CLI_VAULT = "cli_vault"
    BROWSER_EXTENSION = "browser_extension"
    HARDWARE_WALLET = "hardware_wallet"
    LIGHTNING_WALLET = "lightning_wallet"
    PAYREGISTER_DEVICE = "payregister_device"
    ACCESS_CARD = "access_card"
    SERVER_BOT = "server_bot"
    UNKNOWN = "unknown"


class WalletDeviceBindingMethod(StrEnum):
    WALLET_PROOF_REGISTRATION = "wallet_proof_registration"
    WALLET_PROOF_NEW_DEVICE = "wallet_proof_new_device"
    LNURL_AUTH_REGISTRATION = "lnurl_auth_registration"
    LNURL_AUTH_NEW_DEVICE = "lnurl_auth_new_device"
    HARDWARE_WALLET_STEP_UP = "hardware_wallet_step_up"
    AIR_GAPPED_APPROVAL = "air_gapped_approval"
    MULTISIG_QUORUM_APPROVAL = "multisig_quorum_approval"
    RECOVERY_CAPSULE_RESTORE = "recovery_capsule_restore"
    ACCESS_CERTIFICATE_BRIDGE = "access_certificate_bridge"
    TRUSTED_DEVICE_KEY_ROTATION = "trusted_device_key_rotation"


class WalletDeviceStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"
    RECOVERY_ONLY = "recovery_only"


NON_ROOT_OF_TRUST_DEVICE_CLASSES = frozenset({WalletDeviceClass.BROWSER_EXTENSION})


def is_root_of_trust_device_class(device_class: WalletDeviceClass | str) -> bool:
    return WalletDeviceClass(device_class) not in NON_ROOT_OF_TRUST_DEVICE_CLASSES
