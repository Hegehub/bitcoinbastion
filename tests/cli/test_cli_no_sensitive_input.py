from __future__ import annotations

import pytest

from bitcoin_bastion_sdk.errors import BastionSafetyError
from bitcoin_bastion_sdk.safety import assert_safe


@pytest.mark.parametrize("value", ["seed phrase", "mnemonic", "private key", "xprv", "yprv", "zprv", "wallet.dat", "keystore"])
def test_cli_reuses_sdk_sensitive_material_rejection(value: str) -> None:
    with pytest.raises(BastionSafetyError):
        assert_safe(value)
