import pytest

from app.services.wallet_auth.recovery.errors import RecoveryCapsuleError
from app.services.wallet_auth.recovery.redaction import reject_forbidden_recovery_input


@pytest.mark.parametrize("field", ["seed", "mnemonic", "xprv", "private_key"])
def test_lnurl_recovery_rejects_wallet_secret_inputs(field: str) -> None:
    with pytest.raises(RecoveryCapsuleError, match="never asks"):
        reject_forbidden_recovery_input({field: "not-accepted"})
