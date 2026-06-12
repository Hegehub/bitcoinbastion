from __future__ import annotations

import pytest

from bitcoin_bastion_sdk.errors import BastionSafetyError
from bitcoin_bastion_sdk.safety import assert_safe


@pytest.mark.parametrize(
    "value",
    [
        "seed phrase",
        "mnemonic words",
        "private key",
        "xprv123",
        "yprv123",
        "zprv123",
        "wallet.dat",
        "keystore file",
    ],
)
def test_rejects_sensitive_material(value: str) -> None:
    with pytest.raises(BastionSafetyError):
        assert_safe(value)


def test_allows_public_bitcoin_address() -> None:
    assert_safe("bc1qexamplepublicaddress000000000000000000000")
