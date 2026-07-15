from __future__ import annotations

import pytest

from bastion_ui.security.forbidden_inputs import looks_like_sensitive_wallet_material


@pytest.mark.parametrize(
    "value",
    [
        "apple " * 12,
        "abandon " * 24,
        "private key: abc",
        "5" + "K" * 50,
        "xprv9s21ZrQH143K",
        "yprv-example",
        "zprv-example",
        "wallet.dat",
        "keystore",
        "signing material",
    ],
)
def test_sensitive_material_rejected(value: str) -> None:
    assert looks_like_sensitive_wallet_material(value)


def test_public_address_like_input_not_blocked() -> None:
    assert not looks_like_sensitive_wallet_material("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080")
