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


class WalletDeviceStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"
    RECOVERY_ONLY = "recovery_only"


NON_ROOT_OF_TRUST_DEVICE_CLASSES = frozenset({WalletDeviceClass.BROWSER_EXTENSION})


def is_root_of_trust_device_class(device_class: WalletDeviceClass | str) -> bool:
    return WalletDeviceClass(device_class) not in NON_ROOT_OF_TRUST_DEVICE_CLASSES
