import pytest
from app.services.wallet_auth.recovery.redaction import reject_forbidden_recovery_input


def test_seed_and_private_key_inputs_are_rejected() -> None:
    for key in ("seed", "mnemonic", "xprv", "wif", "private_key"):
        with pytest.raises(ValueError):
            reject_forbidden_recovery_input({key: "never-accepted"})
