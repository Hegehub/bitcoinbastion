from __future__ import annotations

from collections.abc import Mapping, Sequence

from bitcoin_bastion_sdk.errors import BastionSafetyError

SAFETY_MESSAGE = (
    "Never submit seed phrases, private keys, wallet files, xprv/yprv/zprv, "
    "or signing material to Bitcoin Bastion."
)
FORBIDDEN_INDICATORS = (
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
    "12 words",
    "24 words",
    "signing material",
)


def assert_safe(value: object) -> None:
    if _contains_sensitive(value):
        raise BastionSafetyError(SAFETY_MESSAGE)


def _contains_sensitive(value: object) -> bool:
    if isinstance(value, str):
        lowered = value.casefold()
        return any(term in lowered for term in FORBIDDEN_INDICATORS)
    if isinstance(value, Mapping):
        return any(_contains_sensitive(str(key)) or _contains_sensitive(item) for key, item in value.items())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return any(_contains_sensitive(item) for item in value)
    return False
