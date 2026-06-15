from __future__ import annotations

import re

from bastion_ui.security.forbidden_inputs import contains_forbidden_material

ADDRESS_REQUIRED = "Address is required."
SENSITIVE_INPUT_REJECTED = "Never enter seed phrases, private keys, wallet files or signing material."
PUBLIC_ADDRESS_REQUIRED = "Input must be a public Bitcoin address."

_BECH32_RE = re.compile(r"^bc1[ac-hj-np-z02-9]{11,87}$", re.IGNORECASE)
_LEGACY_RE = re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$")


def validate_public_bitcoin_address(value: str) -> tuple[bool, str | None]:
    candidate = value.strip()
    if not candidate:
        return False, ADDRESS_REQUIRED
    if contains_forbidden_material(candidate):
        return False, SENSITIVE_INPUT_REJECTED
    if _BECH32_RE.match(candidate) or _LEGACY_RE.match(candidate):
        return True, None
    return False, PUBLIC_ADDRESS_REQUIRED
