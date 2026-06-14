from __future__ import annotations

import pytest

from bastion_mcp.safety import (
    BastionMCPSafetyError,
    assert_no_forbidden_wording,
    assert_no_sensitive_material,
    scan_for_forbidden_wording,
)


@pytest.mark.parametrize(
    "value",
    ["seed phrase", "private key", "xprv", "yprv", "zprv", "wallet.dat", "keystore", "signing material"],
)
def test_sensitive_material_rejected(value: str) -> None:
    with pytest.raises(BastionMCPSafetyError):
        assert_no_sensitive_material({"input": value})


def test_forbidden_wording_detected() -> None:
    assert "guaranteed profit" in scan_for_forbidden_wording("guaranteed profit")
    with pytest.raises(BastionMCPSafetyError):
        assert_no_forbidden_wording({"summary": "price will rise"})
