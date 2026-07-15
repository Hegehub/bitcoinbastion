from __future__ import annotations

import re
from dataclasses import dataclass

from bastion_ui.security.forbidden_inputs import (
    SENSITIVE_WALLET_INPUT_MESSAGE,
    looks_like_sensitive_wallet_material,
)

EMPTY_ADDRESS_MESSAGE = "Enter a public Bitcoin address."
INVALID_ADDRESS_MESSAGE = "Enter a plausible public Bitcoin address beginning with bc1, 1, or 3."

BECH32_RE = re.compile(r"^(bc1)[ac-hj-np-z02-9]{11,87}$", re.IGNORECASE)
LEGACY_RE = re.compile(r"^[13][1-9A-HJ-NP-Za-km-z]{25,39}$")


@dataclass(frozen=True)
class AddressValidationResult:
    ok: bool
    normalized_address: str = ""
    error: str = ""


def normalize_bitcoin_address(value: str) -> str:
    return value.strip()


def is_plausible_public_bitcoin_address(value: str) -> bool:
    normalized = normalize_bitcoin_address(value)
    return bool(BECH32_RE.match(normalized) or LEGACY_RE.match(normalized))


def validate_public_bitcoin_address(value: str) -> AddressValidationResult:
    normalized = normalize_bitcoin_address(value)
    if not normalized:
        return AddressValidationResult(False, error=EMPTY_ADDRESS_MESSAGE)
    if looks_like_sensitive_wallet_material(normalized):
        return AddressValidationResult(False, error=SENSITIVE_WALLET_INPUT_MESSAGE)
    if not is_plausible_public_bitcoin_address(normalized):
        return AddressValidationResult(False, error=INVALID_ADDRESS_MESSAGE)
    return AddressValidationResult(True, normalized_address=normalized)
