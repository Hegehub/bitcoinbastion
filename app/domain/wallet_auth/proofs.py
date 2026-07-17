"""Wallet proof domain enums and strength helpers."""

from __future__ import annotations

from enum import StrEnum


class WalletProofType(StrEnum):
    BIP322 = "bip322"
    LEGACY_MESSAGE_SIGNATURE = "legacy_message_signature"
    HARDWARE_WALLET = "hardware_wallet"
    AIR_GAPPED = "air_gapped"
    MULTISIG_QUORUM = "multisig_quorum"
    LNURL_AUTH = "lnurl_auth"
    ACCESS_CERTIFICATE_BRIDGE = "access_certificate_bridge"


class WalletScriptType(StrEnum):
    P2WPKH = "p2wpkh"
    P2TR = "p2tr"
    P2SH = "p2sh"
    P2WSH = "p2wsh"
    P2PKH = "p2pkh"
    UNKNOWN = "unknown"


class WalletVerificationStrength(StrEnum):
    COMPATIBILITY = "compatibility"
    STANDARD = "standard"
    HIGH_ASSURANCE = "high_assurance"
    SOVEREIGN = "sovereign"


_STRENGTH_RANK = {
    WalletVerificationStrength.COMPATIBILITY: 0,
    WalletVerificationStrength.STANDARD: 1,
    WalletVerificationStrength.HIGH_ASSURANCE: 2,
    WalletVerificationStrength.SOVEREIGN: 3,
}

COMPATIBILITY_ONLY_PROOF_TYPES = frozenset({WalletProofType.LEGACY_MESSAGE_SIGNATURE})


def verification_strength_rank(strength: WalletVerificationStrength | str) -> int:
    return _STRENGTH_RANK[WalletVerificationStrength(strength)]


def is_strength_at_least(
    actual: WalletVerificationStrength | str, required: WalletVerificationStrength | str
) -> bool:
    return verification_strength_rank(actual) >= verification_strength_rank(required)
