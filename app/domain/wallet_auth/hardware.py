"""Hardware-wallet evidence domain vocabulary."""

from __future__ import annotations

from enum import StrEnum


class HardwareWalletEvidenceType(StrEnum):
    NONE = "none"
    SELF_CLAIMED = "self_claimed"
    WALLET_SOFTWARE_REPORT = "wallet_software_report"
    DEVICE_DISPLAY_CONFIRMATION = "device_display_confirmation"
    TRANSPORT_BINDING = "transport_binding"
    VENDOR_ATTESTATION = "vendor_attestation"
    SECURE_ELEMENT_ATTESTATION = "secure_element_attestation"
    TRUSTED_EXECUTION_ATTESTATION = "trusted_execution_attestation"
    AIR_GAPPED_ARTIFACT = "air_gapped_artifact"
    MULTI_DEVICE_QUORUM = "multi_device_quorum"
    UNSUPPORTED = "unsupported"


class HardwareWalletEvidenceStatus(StrEnum):
    ABSENT = "absent"
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNSUPPORTED = "unsupported"


class HardwareWalletAssuranceLevel(StrEnum):
    UNKNOWN = "unknown"
    CLAIMED = "claimed"
    STANDARD = "standard"
    HARDWARE_ASSISTED = "hardware_assisted"
    HARDWARE_VERIFIED = "hardware_verified"
    AIR_GAPPED = "air_gapped"
    SOVEREIGN = "sovereign"


class HardwareWalletInteractionMode(StrEnum):
    USB = "usb"
    NFC = "nfc"
    BLUETOOTH = "bluetooth"
    QR = "qr"
    ANIMATED_QR = "animated_qr"
    SD_CARD = "sd_card"
    FILE_TRANSFER = "file_transfer"
    WEBHID = "webhid"
    WEBUSB = "webusb"
    WALLET_BRIDGE = "wallet_bridge"
    REMOTE_SIGNER = "remote_signer"
    UNKNOWN = "unknown"


class HardwareWalletIntentDisplayState(StrEnum):
    UNKNOWN = "unknown"
    NOT_DISPLAYED = "not_displayed"
    PARTIALLY_DISPLAYED = "partially_displayed"
    FULLY_DISPLAYED = "fully_displayed"
    INDEPENDENTLY_VERIFIED = "independently_verified"


class HardwareWalletBindingType(StrEnum):
    NONE = "none"
    PRINCIPAL_BINDING = "principal_binding"
    DEVICE_BINDING = "device_binding"
    ACCESS_CERTIFICATE_BINDING = "access_certificate_binding"
    RECOVERY_CAPSULE_BINDING = "recovery_capsule_binding"
    BUSINESS_ROLE_BINDING = "business_role_binding"
    PAYREGISTER_OWNER_BINDING = "payregister_owner_binding"


HARDWARE_ASSURANCE_RANK = {
    HardwareWalletAssuranceLevel.UNKNOWN: 0,
    HardwareWalletAssuranceLevel.CLAIMED: 1,
    HardwareWalletAssuranceLevel.STANDARD: 2,
    HardwareWalletAssuranceLevel.HARDWARE_ASSISTED: 3,
    HardwareWalletAssuranceLevel.HARDWARE_VERIFIED: 4,
    HardwareWalletAssuranceLevel.AIR_GAPPED: 5,
    HardwareWalletAssuranceLevel.SOVEREIGN: 6,
}


def hardware_assurance_at_least(actual: HardwareWalletAssuranceLevel | str, required: HardwareWalletAssuranceLevel | str) -> bool:
    return HARDWARE_ASSURANCE_RANK[HardwareWalletAssuranceLevel(actual)] >= HARDWARE_ASSURANCE_RANK[HardwareWalletAssuranceLevel(required)]
