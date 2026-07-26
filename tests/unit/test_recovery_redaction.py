import pytest

from app.services.wallet_auth.recovery.redaction import (
    SAFETY_WARNING,
    reject_forbidden_recovery_input,
)


@pytest.mark.parametrize(
    "payload",
    [
        {"seed": "secret"},
        {"private_key": "secret"},
        {
            "proof": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        },
        {"proof": "xprv-not-real"},
    ],
)
def test_secret_input_rejected_without_echo(payload: dict[str, str]) -> None:
    with pytest.raises(ValueError) as error:
        reject_forbidden_recovery_input(payload)
    assert str(error.value) == SAFETY_WARNING and "secret" not in str(error.value)
